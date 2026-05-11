use std::process::Command;

use serde::Serialize;

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct GitEnvironmentStatus {
    installed: bool,
    version: Option<String>,
    detail: String,
}

fn parse_git_version(stdout: &[u8]) -> Result<String, String> {
    let output = String::from_utf8(stdout.to_vec())
        .map_err(|error| format!("Git 版本输出不是有效的 UTF-8：{error}"))?;
    let version = output.trim().to_string();
    if version.is_empty() {
        return Err("Git 版本输出为空。".to_string());
    }
    Ok(version)
}

fn check_git_environment_sync() -> Result<GitEnvironmentStatus, String> {
    match Command::new("git").arg("--version").output() {
        Ok(output) => {
            if !output.status.success() {
                let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
                let detail = if stderr.is_empty() {
                    format!(
                        "Git 命令执行失败，退出码：{}",
                        output
                            .status
                            .code()
                            .map(|code| code.to_string())
                            .unwrap_or_else(|| "未知".to_string())
                    )
                } else {
                    stderr
                };
                return Ok(GitEnvironmentStatus {
                    installed: false,
                    version: None,
                    detail,
                });
            }

            let version = parse_git_version(&output.stdout)?;
            Ok(GitEnvironmentStatus {
                installed: true,
                version: Some(version.clone()),
                detail: format!("已检测到 Git：{version}"),
            })
        }
        Err(error) => Ok(GitEnvironmentStatus {
            installed: false,
            version: None,
            detail: format!("未找到 Git 命令：{error}"),
        }),
    }
}

#[tauri::command]
pub async fn check_git_environment() -> Result<GitEnvironmentStatus, String> {
    tauri::async_runtime::spawn_blocking(check_git_environment_sync)
        .await
        .map_err(|error| format!("等待 Git 环境检查任务失败：{error}"))?
}
