const { execSync } = require('child_process');
const path = require('path');

const isWin = process.platform === 'win32';
const isMac = process.platform === 'darwin';
const isLinux = process.platform === 'linux';

const python = isWin ? 'python' : 'python3';
const pip = path.join('venv', isWin ? 'Scripts' : 'bin', 'pip');

function run(cmd, opts = {}) {
  console.log(`\n> ${cmd}`);
  execSync(cmd, { stdio: 'inherit', shell: true, ...opts });
}

function hasCommand(cmd) {
  try {
    execSync(isWin ? `where ${cmd}` : `command -v ${cmd}`, { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}

// ---------- 1. Backend venv + deps ----------
console.log('=== Setting up backend venv ===');
run(`${python} -m venv venv`, { cwd: 'backend' });
run(`${pip} install -r requirements.txt`, { cwd: 'backend' });

// ---------- 2. Rust (needed for Tauri) ----------
console.log('\n=== Checking Rust ===');
if (hasCommand('rustc')) {
  console.log('Rust already installed, skipping.');
} else if (isWin) {
  run(`winget install Rustlang.Rustup`);
} else {
  run(`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y`);
}

// ---------- 3. Platform-specific system deps ----------
console.log('\n=== Installing platform dependencies ===');
if (isLinux) {
  run(`sudo apt update`);
  run(
    `sudo apt install -y libwebkit2gtk-4.1-dev build-essential curl wget file ` +
    `libxdo-dev libssl-dev libayatana-appindicator3-dev librsvg2-dev`
  );
} else if (isWin) {
  run(`winget install --silent Microsoft.VisualStudio.2022.BuildTools --override "--add Microsoft.VisualStudio.Workload.VCTools --quiet"`);
  run(`winget install --silent Microsoft.EdgeWebView2Runtime`);
} else if (isMac) {
  try {
    execSync('xcode-select -p', { stdio: 'ignore' });
    console.log('Xcode Command Line Tools already installed, skipping.');
  } catch {
    run(`xcode-select --install`);
  }
}

// ---------- 4. Frontend + Tauri CLI ----------
console.log('\n=== Installing frontend deps + Tauri CLI ===');
run(`npm install`, { cwd: 'frontend' });
run(`npm install --save-dev @tauri-apps/cli`, { cwd: 'frontend' });
run(`npm install @tauri-apps/api`, { cwd: 'frontend' });

console.log('\n=== Setup complete ===');
console.log('Run `npx tauri dev` from the frontend directory to launch the app shell.');

// ---------- 5. Ollama + models ----------
console.log('\n=== Checking Ollama ===');
if (hasCommand('ollama')) {
  console.log('Ollama already installed, skipping install.');
} else if (isWin) {
  run(`winget install --silent Ollama.Ollama`);
} else if (isMac) {
  run(`curl -fsSL https://ollama.com/install.sh | sh`);
} else if (isLinux) {
  run(`curl -fsSL https://ollama.com/install.sh | sh`);
}

console.log('\n=== Pulling required models ===');
const requiredModels = ['qwen2.5:3b'];
for (const model of requiredModels) {
  run(`ollama pull ${model}`);
}