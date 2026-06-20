const https = require('https');
const fs = require('fs');
const path = require('path');

const PUSHDEER_KEY = process.env.PUSHDEER_KEY || '';
const mdFile = path.join(__dirname, 'today_report.md');

var content = fs.readFileSync(mdFile, 'utf8');
var title = '郑公泽·指数投资日报 2026年5月22日';

function tryPushDeer(title, content) {
    return new Promise((resolve) => {
        var data = new URLSearchParams();
        data.append('pushkey', PUSHDEER_KEY);
        data.append('text', title);
        data.append('type', 'markdown');
        data.append('desp', content);
        var req = https.request({
            hostname: 'api2.pushdeer.com',
            path: '/message/push',
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        }, function(res) {
            var b = '';
            res.on('data', function(c) { b += c; });
            res.on('end', function() {
                try {
                    var r = JSON.parse(b);
                    if (r.code === 0) { console.log('PUSH OK:', JSON.stringify(r).substring(0,100)); resolve(true); }
                    else { console.log('PUSH FAIL:', r.code, r.error); resolve(false); }
                } catch(e) { console.log('PARSE ERR:', b.substring(0,100)); resolve(false); }
            });
        });
        req.on('error', function(e) { console.log('REQ ERR:', e.message); resolve(false); });
        req.setTimeout(30000, function() { req.destroy(); resolve(false); });
        req.write(data.toString());
        req.end();
    });
}

(async function() {
    console.log('Content length:', content.length);
    var ok = await tryPushDeer(title, content);
    if (ok) console.log('SUCCESS');
    else console.log('FAILED');
})();