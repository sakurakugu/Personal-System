use std::path::PathBuf;

use serde::{Deserialize, Serialize};

const STORAGE_FILE_NAME: &str = "minecraft-tool.json";

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct MinecraftServerRecord {
    pub address: String,
    pub edition: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[serde(rename_all = "camelCase", default)]
pub struct MinecraftServerStorageData {
    pub favorites: Vec<MinecraftServerRecord>,
    pub history: Vec<MinecraftServerRecord>,
}

fn storage_path() -> PathBuf {
    dirs::home_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join(".personal-system")
        .join(STORAGE_FILE_NAME)
}

fn normalize_record(record: &MinecraftServerRecord) -> Option<MinecraftServerRecord> {
    let address = record.address.trim();
    if address.is_empty() {
        return None;
    }
    let edition = match record.edition.trim() {
        "java" => "java",
        "bedrock" => "bedrock",
        _ => "auto",
    }
    .to_string();
    Some(MinecraftServerRecord {
        address: address.to_string(),
        edition,
    })
}

fn normalize_records(
    records: Vec<MinecraftServerRecord>,
    limit: usize,
) -> Vec<MinecraftServerRecord> {
    let mut output = Vec::new();
    let mut keys = std::collections::HashSet::new();
    for record in records {
        if let Some(record) = normalize_record(&record) {
            let key = format!("{}:{}", record.edition, record.address);
            if keys.insert(key) {
                output.push(record);
            }
        }
        if output.len() >= limit {
            break;
        }
    }
    output
}

#[tauri::command]
pub fn read_minecraft_server_storage() -> Result<MinecraftServerStorageData, String> {
    let path = storage_path();
    let data: MinecraftServerStorageData = crate::support::json_store::read_json_or_default(&path)?;
    Ok(MinecraftServerStorageData {
        favorites: normalize_records(data.favorites, 20),
        history: normalize_records(data.history, 30),
    })
}

#[tauri::command]
pub fn write_minecraft_server_storage(data: MinecraftServerStorageData) -> Result<(), String> {
    let path = storage_path();
    let payload = MinecraftServerStorageData {
        favorites: normalize_records(data.favorites, 20),
        history: normalize_records(data.history, 30),
    };
    crate::support::json_store::write_pretty_json(&path, &payload)
}
