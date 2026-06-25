const https = require('https');

const data = JSON.stringify({
    msg_type: "text",
    content: { text: "郑公泽指数投资日报 - 测试消息" }
});

const options = {
    hostname: 'open.feishu.cn',
    port: 443,
    path: '/open-apis/bot/v2/hook/78352ea0-ceee-4fd9-932b-dafabac15087',
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Content-Length': data.length
    }
};

console.log('正在测试飞书API连接...');
const req = https.request(options, (res) => {
    let body = '';
    res.on('data', chunk => body += chunk);
    res.on('end', () => {
        console.log('状态码:', res.statusCode);
        console.log('响应:', body);
        if (res.statusCode === 200) {
            console.log('✅ 飞书API连接成功！');
        } else {
            console.log('❌ 飞书API连接失败');
        }
    });
});

req.on('error', (e) => {
    console.error('❌ 网络错误:', e.message);
});

req.write(data);
req.end();
