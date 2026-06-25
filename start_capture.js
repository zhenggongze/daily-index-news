const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8765;
const ROOT = path.join(__dirname, '.');

const server = http.createServer((req, res) => {
    let filePath = path.join(ROOT, req.url === '/' ? 'capture_preview.html' : req.url);
    const ext = path.extname(filePath);
    const mime = {'.html':'text/html','.js':'text/javascript','.css':'text/css','.png':'image/png','.jpg':'image/jpeg'};
    fs.readFile(filePath, (err, data) => {
        if (err) { res.writeHead(404); res.end('Not found'); return; }
        res.writeHead(200, {'Content-Type': mime[ext] || 'text/plain'});
        res.end(data);
    });
});

server.listen(PORT, () => {
    console.log('服务器启动: http://localhost:' + PORT);
    const { execSync } = require('child_process');
    try {
        execSync('"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" "http://localhost:' + PORT + '"', { timeout: 3000, stdio: 'ignore' });
    } catch(e) {}
    // 5秒后自动关闭
    setTimeout(() => { server.close(); process.exit(0); }, 30000);
});
