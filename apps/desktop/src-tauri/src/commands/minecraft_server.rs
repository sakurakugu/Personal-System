use std::path::{Path, PathBuf};
use std::process::Command;

use serde::{Deserialize, Serialize};

const MINECRAFT_SERVER_QUERY_RELATIVE_DIR: &[&str] =
    &["apps", "desktop", "python", "minecraft-tool"];

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct MinecraftServerQueryRequest {
    address: String,
    edition: Option<String>,
    timeout: Option<f64>,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct MinecraftServerQueryResult {
    requested_address: String,
    requested_edition: String,
    host: String,
    requested_port: Option<u16>,
    online: bool,
    resolved_edition: Option<String>,
    resolved_port: Option<u16>,
    latency_ms: Option<f64>,
    version_name: Option<String>,
    protocol_version: Option<i64>,
    players_online: Option<i64>,
    players_max: Option<i64>,
    sample_players: Vec<String>,
    description: Option<String>,
    map_name: Option<String>,
    game_mode: Option<String>,
    brand: Option<String>,
    icon: Option<String>,
    error: Option<String>,
}

#[derive(Debug, Clone)]
struct PythonCommandCandidate {
    program: &'static str,
    leading_args: &'static [&'static str],
}

fn get_python_command_candidates() -> &'static [PythonCommandCandidate] {
    &[
        PythonCommandCandidate {
            program: "python",
            leading_args: &[],
        },
        PythonCommandCandidate {
            program: "python3",
            leading_args: &[],
        },
        PythonCommandCandidate {
            program: "py",
            leading_args: &["-3"],
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

    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(parent) = exe_path.parent() {
            roots.push(parent.to_path_buf());
        }
    }

    for root in roots {
        for ancestor in root.ancestors() {
            if is_workspace_root(ancestor) {
                return Some(ancestor.to_path_buf());
            }
        }
    }

    None
}

fn resolve_minecraft_tool_paths() -> Result<(PathBuf, PathBuf), String> {
    let workspace_root =
        resolve_workspace_root().ok_or_else(|| "未找到仓库根目录，无法定位我的世界服务器查询工具。".to_string())?;
    let query_dir = MINECRAFT_SERVER_QUERY_RELATIVE_DIR
        .iter()
        .fold(workspace_root, |path, segment| path.join(segment));

    if !query_dir.exists() {
        return Err(format!(
            "未找到我的世界服务器查询工具目录：{}",
            query_dir.display()
        ));
    }

    let entry_script = query_dir.join("main.py");
    if !entry_script.exists() {
        return Err(format!(
            "未找到我的世界服务器查询入口脚本：{}",
            entry_script.display()
        ));
    }

    Ok((query_dir, entry_script))
}

fn build_query_command_args(
    request: &MinecraftServerQueryRequest,
    entry_script: &Path,
    python_command: &PythonCommandCandidate,
) -> Vec<String> {
    let mut args: Vec<String> = python_command
        .leading_args
        .iter()
        .map(|item| (*item).to_string())
        .collect();

    args.push(entry_script.to_string_lossy().into_owned());
    args.push("query-json".to_string());
    args.push(request.address.trim().to_string());
    args.push("--edition".to_string());
    args.push(
        request
            .edition
            .as_deref()
            .map(str::trim)
            .filter(|value| !value.is_empty())
            .unwrap_or("auto")
            .to_string(),
    );
    args.push("--timeout".to_string());
    args.push(request.timeout.unwrap_or(3.0).to_string());
    args
}

fn run_minecraft_tool_sync(
    request: MinecraftServerQueryRequest,
) -> Result<MinecraftServerQueryResult, String> {
    let address = request.address.trim().to_string();
    if address.is_empty() {
        return Err("服务器地址不能为空。".to_string());
    }

    let python_command =
        resolve_python_command().ok_or_else(|| "未找到可用的 Python 3 命令。".to_string())?;
    let (query_dir, entry_script) = resolve_minecraft_tool_paths()?;
    let command_args = build_query_command_args(&request, &entry_script, &python_command);

    let output = Command::new(python_command.program)
        .args(&command_args)
        .current_dir(&query_dir)
        .output()
        .map_err(|error| format!("执行我的世界服务器查询失败：{error}"))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
        if stderr.is_empty() {
            return Err(format!(
                "我的世界服务器查询失败，退出码：{}",
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
        .map_err(|error| format!("查询结果不是有效的 UTF-8：{error}"))?;
    serde_json::from_str::<MinecraftServerQueryResult>(stdout.trim())
        .map_err(|error| format!("查询结果 JSON 解析失败：{error}"))
}

#[tauri::command]
pub async fn query_minecraft_server(
    request: MinecraftServerQueryRequest,
) -> Result<MinecraftServerQueryResult, String> {
    tauri::async_runtime::spawn_blocking(move || run_minecraft_tool_sync(request))
        .await
        .map_err(|error| format!("等待我的世界服务器查询任务失败：{error}"))?
}
