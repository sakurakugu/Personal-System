use std::fs;
use std::path::PathBuf;

use keyring::Entry;
use serde::{Deserialize, Serialize};

const WIDGET_AUTH_SERVICE: &str = "PersonalSystem.DesktopWidget";
const WIDGET_AUTH_USERNAME: &str = "widget-auth-token";

#[derive(Debug, Serialize, Deserialize)]
#[serde(default)]
struct DesktopWidgetConfigPayload {
    api_base_url: String,
    widget_name: String,
}

impl Default for DesktopWidgetConfigPayload {
    fn default() -> Self {
        Self {
            api_base_url: "http://127.0.0.1:8000/api/v1".to_string(),
            widget_name: "Personal System Widget".to_string(),
        }
    }
}

fn widget_auth_entry() -> Result<Entry, String> {
    Entry::new(WIDGET_AUTH_SERVICE, WIDGET_AUTH_USERNAME).map_err(|error| error.to_string())
}

fn get_widget_config_path() -> Result<PathBuf, String> {
    let base_dir = dirs::config_dir().ok_or_else(|| "无法解析系统配置目录".to_string())?;
    Ok(base_dir
        .join("PersonalSystem")
        .join("desktop-widget")
        .join("config.json"))
}

#[tauri::command]
pub fn sync_widget_auth_token(
    token: String,
    api_base_url: String,
    widget_name: String,
) -> Result<String, String> {
    let normalized_token = token.trim().to_string();
    if normalized_token.is_empty() {
        return Err("小工具凭证不能为空".to_string());
    }

    let normalized_api_base = {
        let value = api_base_url.trim().trim_end_matches('/').to_string();
        if value.is_empty() {
            "http://127.0.0.1:8000/api/v1".to_string()
        } else {
            value
        }
    };
    let normalized_widget_name = {
        let value = widget_name.trim().to_string();
        if value.is_empty() {
            "Personal System Widget".to_string()
        } else {
            value
        }
    };

    let entry = widget_auth_entry()?;
    entry
        .set_password(&normalized_token)
        .map_err(|error| error.to_string())?;

    let config_path = get_widget_config_path()?;
    if let Some(parent) = config_path.parent() {
        fs::create_dir_all(parent).map_err(|error| error.to_string())?;
    }

    let payload = DesktopWidgetConfigPayload {
        api_base_url: normalized_api_base,
        widget_name: normalized_widget_name,
    };
    let content = serde_json::to_string_pretty(&payload).map_err(|error| error.to_string())?;
    fs::write(&config_path, format!("{content}\n")).map_err(|error| error.to_string())?;

    Ok(config_path.display().to_string())
}
