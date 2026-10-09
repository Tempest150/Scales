use std::{net::TcpListener, sync::Mutex};
use tauri::{Manager, RunEvent};
use tauri_plugin_shell::{process::CommandChild, ShellExt};

const DEV_PORT: u16 = 5000; // must match scripts/run-backend.js

struct Backend {
    port: u16,
    child: Mutex<Option<CommandChild>>,
}

#[tauri::command]
fn backend_port(state: tauri::State<Backend>) -> u16 {
    state.port
}

fn free_port() -> u16 {
    TcpListener::bind("127.0.0.1:0").unwrap().local_addr().unwrap().port()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![backend_port])
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            let (port, child) = if cfg!(debug_assertions) {
                // Dev: backend is already running via `npm run backend`
                (DEV_PORT, None)
            } else {
                let port = free_port();
                let (mut rx, child) = app
                    .shell()
                    .sidecar("scales-backend")?
                    .args(["--port", &port.to_string()])
                    .spawn()?;
                tauri::async_runtime::spawn(async move {
                    while let Some(_event) = rx.recv().await {}
                });
                (port, Some(child))
            };

            app.manage(Backend { port, child: Mutex::new(child) });
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|handle, event| {
        if let RunEvent::Exit = event {
            if let Some(b) = handle.try_state::<Backend>() {
                if let Some(child) = b.child.lock().unwrap().take() {
                    let _ = child.kill();
                }
            }
        }
    });
}