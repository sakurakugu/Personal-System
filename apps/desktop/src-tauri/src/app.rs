use tauri::{WebviewUrl, WebviewWindowBuilder};

pub fn build() -> tauri::Builder<tauri::Wry> {
    tauri::Builder::default()
        .setup(|app| {
            let handle = app.handle().clone();
            if let Err(error) = WebviewWindowBuilder::new(
                &handle,
                "desktop-widget",
                WebviewUrl::App("/widget".into()),
            )
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
            {
                let message = error.to_string();
                if !message.contains("already exists") {
                    eprintln!("预创建桌面小工具窗口失败: {message}");
                }
            }
            Ok(())
        })
        .plugin(tauri_plugin_store::Builder::new().build())
        .invoke_handler(tauri::generate_handler![
            crate::commands::auth::load_desktop_auth_token,
            crate::commands::auth::save_desktop_auth_token,
            crate::commands::image_classifier::check_image_classifier_environment,
            crate::commands::image_classifier::select_image_classifier_inputs,
            crate::commands::image_classifier::select_image_classifier_output_path,
            crate::commands::image_classifier::discover_image_classifier_inputs,
            crate::commands::image_classifier::stop_image_classifier,
            crate::commands::image_classifier::run_image_classifier_stream,
            crate::commands::image_classifier::run_image_classifier,
            crate::commands::image_classifier::image_classifier_action,
            crate::commands::image_classifier::image_classifier_result_action,
            crate::commands::minecraft_server::query_minecraft_server,
            crate::commands::minecraft_server_storage::read_minecraft_server_storage,
            crate::commands::minecraft_server_storage::write_minecraft_server_storage,
            crate::commands::window::close_current_window,
            crate::commands::window::close_desktop_widget_window,
            crate::commands::window::open_desktop_main_window,
            crate::commands::window::open_desktop_widget_window,
            crate::commands::windows_tools::check_git_environment,
            crate::commands::widget::sync_widget_auth_token
        ])
}
