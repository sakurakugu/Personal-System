use tauri::{Manager, WebviewUrl, WebviewWindowBuilder};

fn show_and_focus(window: &tauri::WebviewWindow) -> Result<(), String> {
    if window.is_minimized().map_err(|error| error.to_string())? {
        window.unminimize().map_err(|error| error.to_string())?;
    }
    window.show().map_err(|error| error.to_string())?;
    window
        .set_always_on_top(true)
        .map_err(|error| error.to_string())?;
    window.set_focus().map_err(|error| error.to_string())?;
    Ok(())
}

#[tauri::command]
pub fn open_desktop_main_window(app: tauri::AppHandle) -> Result<String, String> {
    let window = app
        .get_webview_window("main")
        .ok_or_else(|| "主窗口不存在".to_string())?;
    show_and_focus(&window)?;
    Ok(window.label().to_string())
}

#[tauri::command]
pub fn open_desktop_widget_window(app: tauri::AppHandle) -> Result<String, String> {
    let window = match app.get_webview_window("desktop-widget") {
        Some(window) => window,
        None => WebviewWindowBuilder::new(&app, "desktop-widget", WebviewUrl::App("/widget".into()))
            .title("桌面小工具")
            .inner_size(380.0, 620.0)
            .min_inner_size(320.0, 480.0)
            .center()
            .decorations(false)
            .resizable(false)
            .skip_taskbar(true)
            .always_on_top(true)
            .visible(false)
            .build()
            .map_err(|error| error.to_string())?,
    };
    show_and_focus(&window)?;
    Ok(window.label().to_string())
}

#[tauri::command]
pub fn close_desktop_widget_window(app: tauri::AppHandle) -> Result<bool, String> {
    let Some(window) = app.get_webview_window("desktop-widget") else {
        return Ok(false);
    };
    window.destroy().map_err(|error| error.to_string())?;
    Ok(true)
}

#[tauri::command]
pub fn close_current_window(window: tauri::WebviewWindow) -> Result<(), String> {
    window.destroy().map_err(|error| error.to_string())
}
