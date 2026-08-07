const { execSync } = require('child_process');
const path = require('path');

const isWin = process.platform === 'win32';
const python = path.join('venv', isWin ? 'Scripts' : 'bin', 'python');

execSync(`${python} app.py`, { cwd: 'backend', stdio: 'inherit', shell: true });
