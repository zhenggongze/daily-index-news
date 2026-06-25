const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3002;
const DIST = path.join(__dirname, 'dist');

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.map': 'application/json',
};

const server = http.createServer((req, res) => {
  let urlPath = req.url.split('?')[0];

  // 去掉 /news/ 前缀，映射到 dist/ 根目录
  if (urlPath.startsWith('/news/')) {
    urlPath = urlPath.slice(5);
  }
  if (!urlPath || urlPath === '/' || urlPath === '/index.html') {
    urlPath = '/index.html';
  }

  const filePath = path.join(DIST, urlPath);
  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Not Found');
      return;
    }
    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
    res.end(data);
  });
});

server.listen(PORT, () => {
  console.log(`📡 新闻站本地服务: http://localhost:${PORT}/news/`);
});
