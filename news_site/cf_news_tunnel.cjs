// Cloudflare Tunnel — 新闻站手机端访问
const { spawn } = require('child_process');

const CF_BIN = 'C:\\Users\\11328817\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\\cloudflared.exe';
const LOCAL_PORT = 3002;

function startTunnel() {
  console.log('启动 Cloudflare Tunnel (新闻站)...');

  const tunnel = spawn(CF_BIN, [
    'tunnel',
    '--url', `http://localhost:${LOCAL_PORT}`,
    '--no-autoupdate'
  ]);

  let foundUrl = false;

  tunnel.stdout.on('data', (data) => {
    const text = data.toString();
    process.stdout.write(text);

    const match = text.match(/https:\/\/[a-z]+-[a-z]+-[a-z0-9]+\.trycloudflare\.com/);
    if (match && !foundUrl) {
      foundUrl = true;
      console.log('');
      console.log('='.repeat(60));
      console.log('  >>> 手机打开: ' + match[0] + '/news/ <<<');
      console.log('  >>> 本地访问: http://localhost:' + LOCAL_PORT + '/news/');
      console.log('='.repeat(60));
      console.log('');
      console.log('保持此窗口打开。按 Ctrl+C 停止。');
    }
  });

  tunnel.stderr.on('data', (data) => {
    process.stderr.write(data);
  });

  tunnel.on('close', (code) => {
    console.log('Tunnel 已断开，退出码:', code);
    console.log('3秒后自动重连...');
    setTimeout(startTunnel, 3000);
  });

  tunnel.on('error', (err) => {
    console.error('启动失败:', err.message);
    console.log('5秒后重试...');
    setTimeout(startTunnel, 5000);
  });
}

startTunnel();
