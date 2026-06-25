const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

const imgPath = path.join(__dirname, 'report.png');
if (!fs.existsSync(imgPath)) {
    console.error('report.png not found');
    process.exit(1);
}

const imgData = fs.readFileSync(imgPath);
const boundary = '----FormBoundary' + Math.random().toString(36).substring(2);
const filename = 'report_' + new Date().toISOString().slice(0, 10) + '.png';

const multipartBody = Buffer.concat([
    Buffer.from('--' + boundary + '\r\nContent-Disposition: form-data; name="file"; filename="' + filename + '"\r\nContent-Type: image/png\r\n\r\n'),
    imgData,
    Buffer.from('\r\n--' + boundary + '--\r\n')
]);

const options = {
    hostname: '0x0.st',
    port: 443,
    path: '/',
    method: 'POST',
    headers: {
        'Content-Type': 'multipart/form-data; boundary=' + boundary,
        'Content-Length': multipartBody.length
    }
};

console.log('Uploading', imgData.length, 'bytes to 0x0.st...');

const req = https.request(options, (res) => {
    let body = '';
    res.on('data', c => body += c);
    res.on('end', () => {
        const url = body.trim();
        if (url.startsWith('http')) {
            console.log('✅ Image URL:', url);
            fs.writeFileSync(path.join(__dirname, 'image_url.txt'), url, 'utf8');
        } else {
            console.error('❌ Upload failed, response:', body.slice(0, 200));
            process.exit(1);
        }
    });
});

req.on('error', (e) => {
    console.error('❌ Network error:', e.message);
    console.log('Trying alternative upload...');
    tryAlternative();
});

req.write(multipartBody);
req.end();

function tryAlternative() {
    const altBody = Buffer.concat([
        Buffer.from('--' + boundary + '\r\nContent-Disposition: form-data; name="image"; filename="' + filename + '"\r\nContent-Type: image/png\r\n\r\n'),
        imgData,
        Buffer.from('\r\n--' + boundary + '--\r\n')
    ]);

    const altOpts = {
        hostname: 'tmpfiles.org',
        port: 443,
        path: '/api/v1/upload',
        method: 'POST',
        headers: {
            'Content-Type': 'multipart/form-data; boundary=' + boundary,
            'Content-Length': altBody.length
        }
    };

    console.log('Trying tmpfiles.org...');
    const req2 = https.request(altOpts, (res) => {
        let body = '';
        res.on('data', c => body += c);
        res.on('end', () => {
            try {
                const json = JSON.parse(body);
                if (json.data && json.data.url) {
                    const url = json.data.url.replace('https://tmpfiles.org/', 'https://tmpfiles.org/dl/');
                    console.log('✅ Image URL:', url);
                    fs.writeFileSync(path.join(__dirname, 'image_url.txt'), url, 'utf8');
                    return;
                }
            } catch(e) {}
            console.error('❌ Alternative also failed:', body.slice(0, 200));
            process.exit(1);
        });
    });
    req2.on('error', (e) => { console.error('❌ All uploads failed'); process.exit(1); });
    req2.write(altBody);
    req2.end();
}
