const { execSync } = require("child_process");
const fs = require("fs");

const run = (cmd) => execSync(cmd, { stdio: "inherit" });
const host = execSync("rustc -Vv").toString().match(/host: (\S+)/)[1];
const ext = process.platform === "win32" ? ".exe" : "";

run("pyinstaller --onefile --name scales-backend backend/main.py");
fs.mkdirSync("src-tauri/binaries", { recursive: true });
fs.copyFileSync(
  `dist/scales-backend${ext}`,
  `src-tauri/binaries/scales-backend-${host}${ext}`
);