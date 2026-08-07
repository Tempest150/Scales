const { execSync } = require('child_process');
const path = require('path');

const isWin = process.platform === 'win32';
const python = isWin ? 'python' : 'python3';
const pip = path.join('venv', isWin ? 'Scripts' : 'bin', 'pip');

execSync(`${python} -m venv venv`, { cwd: 'backend', stdio: 'inherit', shell: true });
execSync(`${pip} install -r requirements.txt`, { cwd: 'backend', stdio: 'inherit', shell: true });
execSync(`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`)
