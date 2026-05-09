use std::io::{BufRead, BufReader, Read};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{LazyLock, Mutex};
use std::thread;
use std::time::{SystemTime, UNIX_EPOCH};

use rfd::FileDialog;
use serde::{Deserialize, Serialize};
use tauri::ipc::Channel;

const IMAGE_CLASSIFIER_RELATIVE_DIR: &[&str] = &["apps", "desktop", "python", "image-classifier"];
static IMAGE_CLASSIFIER_RUNNING_PID: LazyLock<Mutex<Option<u32>>> = LazyLock::new(|| Mutex::new(None));
static IMAGE_CLASSIFIER_CANCEL_REQUESTED: AtomicBool = AtomicBool::new(false);
const IMAGE_CLASSIFIER_STOP_ENV_KEY: &str = "PERSONAL_SYSTEM_IMAGE_CLASSIFIER_STOP_REQUESTED";

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ImageClassifierEnvironmentStatus {
    available: bool,
    workspace_root: Option<String>,
    classifier_dir: Option<String>,
    entry_script: Option<String>,
    python_command: Option<String>,
    python_available: bool,
    ffmpeg_available: bool,
    ffprobe_available: bool,
    missing_dependencies: Vec<String>,
    detail: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ImageClassifierRequestPayload {
    inputs: Vec<String>,
    recursive: bool,
    backend: String,
    base_url: Option<String>,
    model: Option<String>,
    api_key: Option<String>,
    video_frame_count: Option<u32>,
    fail_on_empty: Option<bool>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct ImageClassifierSummaryPayload {
    total: usize,
    classified: usize,
    skipped: usize,
    duration_ms: u64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct ImageClassifierResultItemPayload {
    path: String,
    source_kind: String,
    label: String,
    label_zh: String,
    confidence: f64,
    reason: String,
    raw_response: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct ImageClassifierSkippedItemPayload {
    path: String,
    reason: String,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ImageClassifierRunResult {
    summary: ImageClassifierSummaryPayload,
    results: Vec<ImageClassifierResultItemPayload>,
    skipped: Vec<ImageClassifierSkippedItemPayload>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct ImageClassifierProgressEvent {
    #[serde(rename = "type")]
    event_type: String,
    total: Option<usize>,
    completed: Option<usize>,
    result: Option<ImageClassifierResultItemPayload>,
    item: Option<ImageClassifierSkippedItemPayload>,
    summary: Option<ImageClassifierSummaryPayload>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ImageClassifierSelectInputRequest {
    mode: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ImageClassifierDiscoverInputsRequest {
    inputs: Vec<String>,
    recursive: bool,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ImageClassifierDiscoverInputsResult {
    inputs: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ImageClassifierActionMessagePayload {
    message: String,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ImageClassifierOllamaModelStatePayload {
    loaded: bool,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ImageClassifierActionRequest {
    action: String,
    backend: Option<String>,
    base_url: Option<String>,
    model: Option<String>,
    api_key: Option<String>,
    should_load: Option<bool>,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ImageClassifierActionResult {
    message: Option<String>,
    loaded: Option<bool>,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ImageClassifierResultActionPayload {
    results: Vec<ImageClassifierResultItemPayload>,
    skipped: Vec<ImageClassifierSkippedItemPayload>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ImageClassifierResultActionRequest {
    action: String,
    payload: ImageClassifierResultActionPayload,
    output_path: String,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ImageClassifierResultActionResult {
    message: String,
    results: Option<Vec<ImageClassifierResultItemPayload>>,
    skipped: Option<Vec<ImageClassifierSkippedItemPayload>>,
}

#[derive(Debug, Clone)]
struct PythonCommandCandidate {
    program: &'static str,
    leading_args: &'static [&'static str],
    display_name: &'static str,
}

fn get_python_command_candidates() -> &'static [PythonCommandCandidate] {
    &[
        PythonCommandCandidate {
            program: "python",
            leading_args: &[],
            display_name: "python",
        },
        PythonCommandCandidate {
            program: "python3",
            leading_args: &[],
            display_name: "python3",
        },
        PythonCommandCandidate {
            program: "py",
            leading_args: &["-3"],
            display_name: "py -3",
        },
    ]
}

fn command_works(program: &str, args: &[&str]) -> bool {
    match Command::new(program).args(args).output() {
        Ok(output) => output.status.success(),
        Err(_) => false,
    }
}

fn resolve_python_command() -> Option<PythonCommandCandidate> {
    for candidate in get_python_command_candidates() {
        let mut version_args = candidate.leading_args.to_vec();
        version_args.push("--version");
        if command_works(candidate.program, &version_args) {
            return Some(candidate.clone());
        }
    }
    None
}

fn is_workspace_root(candidate: &Path) -> bool {
    candidate.join("apps").join("desktop").exists() && candidate.join("packages").exists()
}

fn resolve_workspace_root() -> Option<PathBuf> {
    let mut roots: Vec<PathBuf> = Vec::new();

    if let Ok(current_dir) = std::env::current_dir() {
        roots.push(current_dir);
    }
    if let Ok(current_exe) = std::env::current_exe() {
        if let Some(parent) = current_exe.parent() {
            roots.push(parent.to_path_buf());
        }
    }

    for root in roots {
        for ancestor in root.ancestors() {
            let candidate = ancestor.to_path_buf();
            if is_workspace_root(&candidate) {
                return Some(candidate);
            }
        }
    }

    None
}

fn resolve_image_classifier_paths() -> Result<(PathBuf, PathBuf), String> {
    let workspace_root = resolve_workspace_root()
        .ok_or_else(|| "未能定位仓库根目录，当前仅支持在源码仓库内运行图片分类工具。".to_string())?;
    let classifier_dir = IMAGE_CLASSIFIER_RELATIVE_DIR
        .iter()
        .fold(workspace_root.clone(), |current, part| current.join(part));
    let entry_script = classifier_dir.join("main.py");

    if !classifier_dir.exists() {
        return Err(format!(
            "未找到图片分类目录：{}",
            classifier_dir.display()
        ));
    }
    if !entry_script.exists() {
        return Err(format!(
            "未找到图片分类入口脚本：{}",
            entry_script.display()
        ));
    }

    Ok((classifier_dir, entry_script))
}

fn build_python_entry_command_args(
    subcommand: &str,
    entry_script: &Path,
    python_command: &PythonCommandCandidate,
) -> Vec<String> {
    let mut args: Vec<String> = python_command
        .leading_args
        .iter()
        .map(|value| (*value).to_string())
        .collect();
    args.push(entry_script.display().to_string());
    args.push(subcommand.to_string());
    args
}

fn append_remote_backend_args(
    args: &mut Vec<String>,
    backend: &str,
    base_url: Option<&str>,
    model: Option<&str>,
    api_key: Option<&str>,
) {
    args.push("--backend".to_string());
    args.push(if backend.trim().is_empty() {
        "mock".to_string()
    } else {
        backend.trim().to_string()
    });

    if let Some(value) = base_url.map(str::trim).filter(|value| !value.is_empty()) {
        args.push("--base-url".to_string());
        args.push(value.to_string());
    }
    if let Some(value) = model.map(str::trim).filter(|value| !value.is_empty()) {
        args.push("--model".to_string());
        args.push(value.to_string());
    }
    if let Some(value) = api_key.map(str::trim).filter(|value| !value.is_empty()) {
        args.push("--api-key".to_string());
        args.push(value.to_string());
    }
}

fn build_image_classifier_command_args(
    subcommand: &str,
    request: &ImageClassifierRequestPayload,
    entry_script: &Path,
    python_command: &PythonCommandCandidate,
) -> Vec<String> {
    let mut args = build_python_entry_command_args(subcommand, entry_script, python_command);
    args.extend(request.inputs.iter().cloned());

    if !request.recursive {
        args.push("--no-recursive".to_string());
    }

    append_remote_backend_args(
        &mut args,
        &request.backend,
        request.base_url.as_deref(),
        request.model.as_deref(),
        request.api_key.as_deref(),
    );

    args.push("--video-frame-count".to_string());
    args.push(request.video_frame_count.unwrap_or(5).to_string());

    if request.fail_on_empty.unwrap_or(false) {
        args.push("--fail-on-empty".to_string());
    }

    args
}

fn apply_image_classifier_stop_env(command: &mut Command) {
    command.env(
        IMAGE_CLASSIFIER_STOP_ENV_KEY,
        if IMAGE_CLASSIFIER_CANCEL_REQUESTED.load(Ordering::SeqCst) {
            "1"
        } else {
            "0"
        },
    );
}

fn build_discover_inputs_command_args(
    request: &ImageClassifierDiscoverInputsRequest,
    entry_script: &Path,
    python_command: &PythonCommandCandidate,
) -> Vec<String> {
    let mut args = build_python_entry_command_args("discover-json", entry_script, python_command);
    args.extend(request.inputs.iter().cloned());
    if !request.recursive {
        args.push("--no-recursive".to_string());
    }
    args
}

fn build_action_command_args(
    action: &str,
    backend: Option<&str>,
    base_url: Option<&str>,
    model: Option<&str>,
    api_key: Option<&str>,
    should_load: Option<bool>,
    entry_script: &Path,
    python_command: &PythonCommandCandidate,
) -> Vec<String> {
    let mut args = build_python_entry_command_args("action-json", entry_script, python_command);
    args.push("--action".to_string());
    args.push(action.to_string());
    append_remote_backend_args(
        &mut args,
        backend.unwrap_or("mock"),
        base_url,
        model,
        api_key,
    );
    if let Some(value) = should_load {
        args.push("--should-load".to_string());
        args.push(if value { "true".to_string() } else { "false".to_string() });
    }
    args
}

fn build_result_action_command_args(
    action: &str,
    payload_file: &Path,
    output_path: &Path,
    entry_script: &Path,
    python_command: &PythonCommandCandidate,
) -> Vec<String> {
    let mut args = build_python_entry_command_args("result-action-json", entry_script, python_command);
    args.push("--action".to_string());
    args.push(action.to_string());
    args.push("--payload-file".to_string());
    args.push(payload_file.display().to_string());
    args.push("--output-path".to_string());
    args.push(output_path.display().to_string());
    args
}

fn run_image_classifier_python_command<T: for<'de> Deserialize<'de>>(
    command_args: Vec<String>,
    error_prefix: &str,
) -> Result<T, String> {
    let python_command =
        resolve_python_command().ok_or_else(|| "未找到可用的 Python 3 命令。".to_string())?;
    let (classifier_dir, _) = resolve_image_classifier_paths()?;

    let output = Command::new(python_command.program)
        .args(&command_args)
        .current_dir(&classifier_dir)
        .output()
        .map_err(|error| format!("{error_prefix}：{error}"))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
        if stderr.is_empty() {
            return Err(format!("{error_prefix}。"));
        }
        return Err(stderr);
    }

    let stdout = String::from_utf8(output.stdout)
        .map_err(|error| format!("{error_prefix}结果不是有效的 UTF-8：{error}"))?;
    serde_json::from_str::<T>(stdout.trim())
        .map_err(|error| format!("{error_prefix}结果 JSON 解析失败：{error}"))
}

fn create_temp_result_payload_file(payload: &ImageClassifierResultActionPayload) -> Result<PathBuf, String> {
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|error| format!("生成临时文件时间戳失败：{error}"))?
        .as_millis();
    let payload_path = std::env::temp_dir().join(format!("personal-system-image-classifier-{timestamp}.json"));
    let content = serde_json::to_string(payload)
        .map_err(|error| format!("序列化图片分类结果失败：{error}"))?;
    std::fs::write(&payload_path, content)
        .map_err(|error| format!("写入图片分类临时结果失败：{error}"))?;
    Ok(payload_path)
}

fn set_running_image_classifier_pid(pid: Option<u32>) -> Result<(), String> {
    let mut guard = IMAGE_CLASSIFIER_RUNNING_PID
        .lock()
        .map_err(|_| "图片分类任务状态锁已损坏。".to_string())?;
    *guard = pid;
    Ok(())
}

fn is_process_running(pid: u32) -> bool {
    #[cfg(target_os = "windows")]
    {
        Command::new("tasklist")
            .args(["/FI", &format!("PID eq {pid}")])
            .output()
            .map(|output| {
                output.status.success()
                    && String::from_utf8_lossy(&output.stdout).contains(&pid.to_string())
            })
            .unwrap_or(false)
    }

    #[cfg(not(target_os = "windows"))]
    {
        Command::new("kill")
            .args(["-0", &pid.to_string()])
            .output()
            .map(|output| output.status.success())
            .unwrap_or(false)
    }
}

fn get_running_image_classifier_pid() -> Result<Option<u32>, String> {
    let mut guard = IMAGE_CLASSIFIER_RUNNING_PID
        .lock()
        .map_err(|_| "图片分类任务状态锁已损坏。".to_string())?;
    if let Some(pid) = *guard {
        if !is_process_running(pid) {
            *guard = None;
            return Ok(None);
        }
    }
    Ok(*guard)
}

fn clear_running_image_classifier_pid_if_matches(pid: u32) -> Result<(), String> {
    let mut guard = IMAGE_CLASSIFIER_RUNNING_PID
        .lock()
        .map_err(|_| "图片分类任务状态锁已损坏。".to_string())?;
    if guard.as_ref() == Some(&pid) {
        *guard = None;
    }
    Ok(())
}

fn terminate_process_tree(pid: u32) -> Result<(), String> {
    #[cfg(target_os = "windows")]
    {
        let output = Command::new("taskkill")
            .args(["/PID", &pid.to_string(), "/T", "/F"])
            .output()
            .map_err(|error| format!("停止图片分类任务失败：{error}"))?;
        if output.status.success() {
            return Ok(());
        }
        let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
        if stderr.is_empty() {
            return Err("停止图片分类任务失败。".to_string());
        }
        return Err(stderr);
    }

    #[cfg(not(target_os = "windows"))]
    {
        let output = Command::new("kill")
            .args(["-TERM", &pid.to_string()])
            .output()
            .map_err(|error| format!("停止图片分类任务失败：{error}"))?;
        if output.status.success() {
            return Ok(());
        }
        let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
        if stderr.is_empty() {
            return Err("停止图片分类任务失败。".to_string());
        }
        Err(stderr)
    }
}

fn read_image_classifier_stderr(stderr: impl Read + Send + 'static) -> thread::JoinHandle<Result<String, String>> {
    thread::spawn(move || {
        let mut stderr_reader = BufReader::new(stderr);
        let mut stderr_content = String::new();
        stderr_reader
            .read_to_string(&mut stderr_content)
            .map_err(|error| format!("读取图片分类任务错误输出失败：{error}"))?;
        Ok(stderr_content)
    })
}

fn join_image_classifier_stderr(
    stderr_handle: thread::JoinHandle<Result<String, String>>,
) -> Result<String, String> {
    stderr_handle
        .join()
        .map_err(|_| "读取图片分类任务错误输出线程异常退出。".to_string())?
}

#[tauri::command]
pub fn select_image_classifier_inputs(
    request: ImageClassifierSelectInputRequest,
) -> Result<Vec<String>, String> {
    let dialog = FileDialog::new().set_title(match request.mode.trim() {
        "file" => "选择图片或视频",
        "folder" => "选择文件夹",
        _ => return Err("不支持的选择模式。".to_string()),
    });

    match request.mode.trim() {
        "file" => {
            let files = dialog
                .add_filter(
                    "Media",
                    &[
                        "png", "jpg", "jpeg", "webp", "bmp", "gif", "heic", "heif", "avif", "mp4",
                        "mov", "mkv", "avi", "webm", "m4v",
                    ],
                )
                .pick_files()
                .unwrap_or_default();
            Ok(files
                .into_iter()
                .map(|path| path.display().to_string())
                .collect())
        }
        "folder" => Ok(dialog
            .pick_folder()
            .map(|path| vec![path.display().to_string()])
            .unwrap_or_default()),
        _ => Err("不支持的选择模式。".to_string()),
    }
}

#[tauri::command]
pub fn select_image_classifier_output_path(mode: String) -> Result<Option<String>, String> {
    let dialog = FileDialog::new().set_title(match mode.trim() {
        "csv" => "导出 CSV",
        "json" => "导出 JSON",
        "folder" => "选择分类输出文件夹",
        _ => return Err("不支持的输出选择模式。".to_string()),
    });

    match mode.trim() {
        "csv" => Ok(dialog
            .add_filter("CSV", &["csv"])
            .set_file_name("image-classifier-results.csv")
            .save_file()
            .map(|path| path.display().to_string())),
        "json" => Ok(dialog
            .add_filter("JSON", &["json"])
            .set_file_name("image-classifier-results.json")
            .save_file()
            .map(|path| path.display().to_string())),
        "folder" => Ok(dialog
            .pick_folder()
            .map(|path| path.display().to_string())),
        _ => Err("不支持的输出选择模式。".to_string()),
    }
}

#[tauri::command]
pub fn check_image_classifier_environment() -> Result<ImageClassifierEnvironmentStatus, String> {
    let workspace_root = resolve_workspace_root();
    let path_result = resolve_image_classifier_paths();
    let python_command = resolve_python_command();
    let ffmpeg_available = command_works("ffmpeg", &["-version"]);
    let ffprobe_available = command_works("ffprobe", &["-version"]);

    let mut missing_dependencies: Vec<String> = Vec::new();
    if python_command.is_none() {
        missing_dependencies.push("Python 3".to_string());
    }
    if !ffmpeg_available {
        missing_dependencies.push("ffmpeg".to_string());
    }
    if !ffprobe_available {
        missing_dependencies.push("ffprobe".to_string());
    }
    if let Err(error) = &path_result {
        missing_dependencies.push(error.clone());
    }

    let detail = if missing_dependencies.is_empty() {
        "图片分类运行环境检查通过。".to_string()
    } else {
        format!("图片分类运行环境不完整：{}", missing_dependencies.join("；"))
    };

    let (classifier_dir, entry_script) = match path_result {
        Ok((classifier_dir, entry_script)) => (
            Some(classifier_dir.display().to_string()),
            Some(entry_script.display().to_string()),
        ),
        Err(_) => (None, None),
    };

    let python_available = python_command.is_some();
    let python_command_name = python_command
        .as_ref()
        .map(|candidate| candidate.display_name.to_string());

    Ok(ImageClassifierEnvironmentStatus {
        available: missing_dependencies.is_empty(),
        workspace_root: workspace_root.map(|path| path.display().to_string()),
        classifier_dir,
        entry_script,
        python_command: python_command_name,
        python_available,
        ffmpeg_available,
        ffprobe_available,
        missing_dependencies,
        detail,
    })
}

#[tauri::command]
pub fn discover_image_classifier_inputs(
    request: ImageClassifierDiscoverInputsRequest,
) -> Result<ImageClassifierDiscoverInputsResult, String> {
    if request.inputs.is_empty() {
        return Ok(ImageClassifierDiscoverInputsResult { inputs: Vec::new() });
    }

    let python_command =
        resolve_python_command().ok_or_else(|| "未找到可用的 Python 3 命令。".to_string())?;
    let (classifier_dir, entry_script) = resolve_image_classifier_paths()?;
    let command_args =
        build_discover_inputs_command_args(&request, &entry_script, &python_command);

    let output = Command::new(python_command.program)
        .args(&command_args)
        .current_dir(&classifier_dir)
        .output()
        .map_err(|error| format!("发现图片分类输入失败：{error}"))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
        if stderr.is_empty() {
            return Err("发现图片分类输入失败。".to_string());
        }
        return Err(stderr);
    }

    let stdout = String::from_utf8(output.stdout)
        .map_err(|error| format!("发现输入结果不是有效的 UTF-8：{error}"))?;
    serde_json::from_str::<ImageClassifierDiscoverInputsResult>(stdout.trim())
        .map_err(|error| format!("发现输入结果 JSON 解析失败：{error}"))
}

#[tauri::command]
pub fn stop_image_classifier() -> Result<(), String> {
    get_running_image_classifier_pid()?
        .ok_or_else(|| "当前没有正在运行的图片分类任务。".to_string())?;
    IMAGE_CLASSIFIER_CANCEL_REQUESTED.store(true, Ordering::SeqCst);
    Ok(())
}

fn run_image_classifier_stream_sync(
    inputs: Vec<String>,
    recursive: bool,
    backend: String,
    base_url: Option<String>,
    model: Option<String>,
    api_key: Option<String>,
    video_frame_count: Option<u32>,
    fail_on_empty: Option<bool>,
    on_event: Channel<ImageClassifierProgressEvent>,
) -> Result<(), String> {
    let request = ImageClassifierRequestPayload {
        inputs,
        recursive,
        backend,
        base_url,
        model,
        api_key,
        video_frame_count,
        fail_on_empty,
    };

    if request.inputs.is_empty() {
        return Err("至少需要传入一个文件或目录路径。".to_string());
    }
    if get_running_image_classifier_pid()?.is_some() {
        return Err("已有图片分类任务在运行中。".to_string());
    }

    let python_command =
        resolve_python_command().ok_or_else(|| "未找到可用的 Python 3 命令。".to_string())?;
    let (classifier_dir, entry_script) = resolve_image_classifier_paths()?;
    let command_args =
        build_image_classifier_command_args("desktop-stream-json", &request, &entry_script, &python_command);

    IMAGE_CLASSIFIER_CANCEL_REQUESTED.store(false, Ordering::SeqCst);
    let mut command = Command::new(python_command.program);
    command
        .args(&command_args)
        .current_dir(&classifier_dir)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    apply_image_classifier_stop_env(&mut command);
    let mut child = command
        .spawn()
        .map_err(|error| format!("启动图片分类任务失败：{error}"))?;
    let pid = child.id();
    set_running_image_classifier_pid(Some(pid))?;

    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| "无法读取图片分类任务标准输出。".to_string())?;
    let stderr = child
        .stderr
        .take()
        .ok_or_else(|| "无法读取图片分类任务错误输出。".to_string())?;

    let stderr_handle = read_image_classifier_stderr(stderr);
    let stdout_reader = BufReader::new(stdout);

    let stream_result: Result<(), String> = (|| {
        for line in stdout_reader.lines() {
            let content = line.map_err(|error| format!("读取图片分类进度失败：{error}"))?;
            let trimmed = content.trim();
            if trimmed.is_empty() {
                continue;
            }
            let event = serde_json::from_str::<ImageClassifierProgressEvent>(trimmed)
                .map_err(|error| format!("解析图片分类进度事件失败：{error}"))?;
            on_event
                .send(event)
                .map_err(|error| format!("发送图片分类进度事件失败：{error}"))?;
        }
        Ok(())
    })();

    if let Err(error) = &stream_result {
        let _ = terminate_process_tree(pid);
        let _ = child.wait();
        let _ = join_image_classifier_stderr(stderr_handle);
        clear_running_image_classifier_pid_if_matches(pid)?;
        IMAGE_CLASSIFIER_CANCEL_REQUESTED.store(false, Ordering::SeqCst);
        return Err(error.clone());
    }

    let output = child
        .wait()
        .map_err(|error| format!("读取图片分类任务结果失败：{error}"))?;
    clear_running_image_classifier_pid_if_matches(pid)?;

    if !output.success() {
        if IMAGE_CLASSIFIER_CANCEL_REQUESTED.swap(false, Ordering::SeqCst) {
            let _ = join_image_classifier_stderr(stderr_handle);
            return Err("图片分类已停止。".to_string());
        }
        let stderr_content = join_image_classifier_stderr(stderr_handle)?;
        let trimmed_stderr = stderr_content.trim().to_string();
        if trimmed_stderr.is_empty() {
            return Err("图片分类任务执行失败。".to_string());
        }
        return Err(trimmed_stderr);
    }

    let _ = join_image_classifier_stderr(stderr_handle);
    IMAGE_CLASSIFIER_CANCEL_REQUESTED.store(false, Ordering::SeqCst);
    Ok(())
}

#[tauri::command]
pub async fn run_image_classifier_stream(
    inputs: Vec<String>,
    recursive: bool,
    backend: String,
    base_url: Option<String>,
    model: Option<String>,
    api_key: Option<String>,
    video_frame_count: Option<u32>,
    fail_on_empty: Option<bool>,
    on_event: Channel<ImageClassifierProgressEvent>,
) -> Result<(), String> {
    tauri::async_runtime::spawn_blocking(move || {
        run_image_classifier_stream_sync(
            inputs,
            recursive,
            backend,
            base_url,
            model,
            api_key,
            video_frame_count,
            fail_on_empty,
            on_event,
        )
    })
    .await
    .map_err(|error| format!("等待图片分类任务失败：{error}"))?
}

fn run_image_classifier_sync(
    request: ImageClassifierRequestPayload,
) -> Result<ImageClassifierRunResult, String> {
    if request.inputs.is_empty() {
        return Err("至少需要传入一个文件或目录路径。".to_string());
    }

    let python_command =
        resolve_python_command().ok_or_else(|| "未找到可用的 Python 3 命令。".to_string())?;
    let (classifier_dir, entry_script) = resolve_image_classifier_paths()?;
    let command_args =
        build_image_classifier_command_args("desktop-json", &request, &entry_script, &python_command);

    if get_running_image_classifier_pid()?.is_some() {
        return Err("已有图片分类任务在运行中。".to_string());
    }

    IMAGE_CLASSIFIER_CANCEL_REQUESTED.store(false, Ordering::SeqCst);
    let child = Command::new(python_command.program)
        .args(&command_args)
        .current_dir(&classifier_dir)
        .spawn()
        .map_err(|error| format!("启动图片分类任务失败：{error}"))?;
    let pid = child.id();
    set_running_image_classifier_pid(Some(pid))?;
    let output = child
        .wait_with_output()
        .map_err(|error| format!("读取图片分类任务结果失败：{error}"))?;
    clear_running_image_classifier_pid_if_matches(pid)?;

    if !output.status.success() {
        if IMAGE_CLASSIFIER_CANCEL_REQUESTED.swap(false, Ordering::SeqCst) {
            return Err("图片分类已停止。".to_string());
        }
        let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
        if stderr.is_empty() {
            return Err(format!(
                "图片分类任务执行失败，退出码：{}",
                output
                    .status
                    .code()
                    .map(|code| code.to_string())
                    .unwrap_or_else(|| "未知".to_string())
            ));
        }
        return Err(stderr);
    }

    let stdout = String::from_utf8(output.stdout)
        .map_err(|error| format!("图片分类结果不是有效的 UTF-8：{error}"))?;
    IMAGE_CLASSIFIER_CANCEL_REQUESTED.store(false, Ordering::SeqCst);
    serde_json::from_str::<ImageClassifierRunResult>(stdout.trim())
        .map_err(|error| format!("图片分类结果 JSON 解析失败：{error}"))
}

#[tauri::command]
pub async fn run_image_classifier(
    request: ImageClassifierRequestPayload,
) -> Result<ImageClassifierRunResult, String> {
    tauri::async_runtime::spawn_blocking(move || run_image_classifier_sync(request))
        .await
        .map_err(|error| format!("等待图片分类任务失败：{error}"))?
}

#[tauri::command]
pub fn image_classifier_action(
    request: ImageClassifierActionRequest,
) -> Result<ImageClassifierActionResult, String> {
    let python_command =
        resolve_python_command().ok_or_else(|| "未找到可用的 Python 3 命令。".to_string())?;
    let (_, entry_script) = resolve_image_classifier_paths()?;
    let action = request.action.trim();

    match action {
        "test_connection" => {
            let command_args = build_action_command_args(
                "test_connection",
                request.backend.as_deref(),
                request.base_url.as_deref(),
                request.model.as_deref(),
                request.api_key.as_deref(),
                None,
                &entry_script,
                &python_command,
            );
            let payload = run_image_classifier_python_command::<ImageClassifierActionMessagePayload>(
                command_args,
                "测试图片分类后端连接失败",
            )?;
            Ok(ImageClassifierActionResult {
                message: Some(payload.message),
                loaded: None,
            })
        }
        "start_ollama" => {
            let command_args = build_action_command_args(
                "start_ollama",
                Some("ollama"),
                request.base_url.as_deref(),
                request.model.as_deref(),
                request.api_key.as_deref(),
                None,
                &entry_script,
                &python_command,
            );
            let payload = run_image_classifier_python_command::<ImageClassifierActionMessagePayload>(
                command_args,
                "启动 Ollama 失败",
            )?;
            Ok(ImageClassifierActionResult {
                message: Some(payload.message),
                loaded: None,
            })
        }
        "toggle_ollama_model" => {
            let should_load = request
                .should_load
                .ok_or_else(|| "切换 Ollama 模型状态缺少目标状态。".to_string())?;
            let command_args = build_action_command_args(
                "toggle_ollama_model",
                Some("ollama"),
                request.base_url.as_deref(),
                request.model.as_deref(),
                request.api_key.as_deref(),
                Some(should_load),
                &entry_script,
                &python_command,
            );
            let payload = run_image_classifier_python_command::<ImageClassifierActionMessagePayload>(
                command_args,
                "切换 Ollama 模型状态失败",
            )?;
            Ok(ImageClassifierActionResult {
                message: Some(payload.message),
                loaded: None,
            })
        }
        "get_ollama_model_state" => {
            let command_args = build_action_command_args(
                "get_ollama_model_state",
                Some("ollama"),
                request.base_url.as_deref(),
                request.model.as_deref(),
                request.api_key.as_deref(),
                None,
                &entry_script,
                &python_command,
            );
            let payload = run_image_classifier_python_command::<ImageClassifierOllamaModelStatePayload>(
                command_args,
                "查询 Ollama 模型状态失败",
            )?;
            Ok(ImageClassifierActionResult {
                message: None,
                loaded: Some(payload.loaded),
            })
        }
        _ => Err(format!("不支持的图片分类动作：{action}")),
    }
}

#[tauri::command]
pub fn image_classifier_result_action(
    request: ImageClassifierResultActionRequest,
) -> Result<ImageClassifierResultActionResult, String> {
    let python_command =
        resolve_python_command().ok_or_else(|| "未找到可用的 Python 3 命令。".to_string())?;
    let (_, entry_script) = resolve_image_classifier_paths()?;
    let action = request.action.trim();
    let output_path = PathBuf::from(request.output_path.trim());

    if output_path.as_os_str().is_empty() {
        return Err("输出路径不能为空。".to_string());
    }

    let payload_file = create_temp_result_payload_file(&request.payload)?;
    let command_args = build_result_action_command_args(
        action,
        &payload_file,
        &output_path,
        &entry_script,
        &python_command,
    );
    let result = run_image_classifier_python_command::<ImageClassifierResultActionResult>(
        command_args,
        "执行图片分类结果处理失败",
    );
    let _ = std::fs::remove_file(&payload_file);
    result
}
