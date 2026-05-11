mod app;
mod commands;
mod support;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    app::build()
        .run(tauri::generate_context!())
        .expect("启动桌面端失败");
}
