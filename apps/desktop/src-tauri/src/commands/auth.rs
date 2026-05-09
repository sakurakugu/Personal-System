use keyring::Entry;

const DESKTOP_AUTH_SERVICE: &str = "PersonalSystem.Desktop";
const DESKTOP_AUTH_USERNAME: &str = "desktop-auth-token";

fn desktop_auth_entry() -> Result<Entry, String> {
    Entry::new(DESKTOP_AUTH_SERVICE, DESKTOP_AUTH_USERNAME).map_err(|error| error.to_string())
}

#[tauri::command]
pub fn load_desktop_auth_token() -> Result<Option<String>, String> {
    let entry = desktop_auth_entry()?;
    match entry.get_password() {
        Ok(value) => {
            let normalized = value.trim().to_string();
            if normalized.is_empty() {
                Ok(None)
            } else {
                Ok(Some(normalized))
            }
        }
        Err(keyring::Error::NoEntry) => Ok(None),
        Err(error) => Err(error.to_string()),
    }
}

#[tauri::command]
pub fn save_desktop_auth_token(token: Option<String>) -> Result<(), String> {
    let entry = desktop_auth_entry()?;
    let normalized = token
        .as_deref()
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .map(ToOwned::to_owned);

    match normalized {
        Some(value) => entry
            .set_password(&value)
            .map_err(|error| error.to_string()),
        None => match entry.delete_credential() {
            Ok(()) | Err(keyring::Error::NoEntry) => Ok(()),
            Err(error) => Err(error.to_string()),
        },
    }
}
