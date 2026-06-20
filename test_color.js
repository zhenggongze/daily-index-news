const https = require('https');
process.env.HTTP_PROXY = '';
process.env.HTTPS_PROXY = '';
process.env.NO_PROXY = '*';

const KEY = process.env.PUSHDEER_KEY || '';

var body = 'pushkey=' + KEY + '&text=颜色测试&type=markdown&desp=' + encodeURIComponent(
  '# 颜色测试\n\n' +
  '<font color="red">🔴 红色文字</font>\n\n' +
  '<font color="blue">🔵 蓝色文字</font>\n\n' +
  '<font color="green">🟢 绿色文字</font>\n\n' +
  '<font color="#FF6600">🟠 橙色文字</font>\n\n' +
  '<font color="#888888">⚪ 灰色文字</font>\n\n' +
  '---\n\n' +
  '**加粗标题**\n\n' +
  '普通正文\n\n' +
  '> 引用区块'
);

var req = https.request({
  hostname: 'api2.pushdeer.com',
  path: '/message/push',
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'Content-Length': Buffer.byteLength(body) }
}, function(r) {
  var b = '';
  r.on('data', function(c) { b += c; });
  r.on('end', function() { console.log(b); });
});
req.write(body);
req.end();