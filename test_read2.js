
const fs = require('fs');
const path = require('path');

const REPORT_PATH = path.join(__dirname, 'today_report.md');
console.log('Reading file from absolute path:', REPORT_PATH);
console.log('Dirname:', __dirname);
console.log('File exists:', fs.existsSync(REPORT_PATH));

if (fs.existsSync(REPORT_PATH)) {
    const stats = fs.statSync(REPORT_PATH);
    console.log('File stats:');
    console.log('  Size:', stats.size, 'bytes');
    console.log('  Modified:', stats.mtime);
    console.log('  Created:', stats.birthtime);
    
    // 尝试直接用绝对路径读
    const content = fs.readFileSync(REPORT_PATH, { encoding: 'utf8' });
    console.log('\nFirst 200 chars of content:');
    console.log(content.substring(0, 200));
    
    // 同时列出目录下的所有文件，看看有没有多个 today_report.md
    console.log('\nFiles in directory:');
    const files = fs.readdirSync(__dirname);
    for (let i = 0; i &lt; files.length; i++) {
        const file = files[i];
        if (file.toLowerCase().indexOf('today_report') &gt;= 0) {
            console.log('  -', file);
        }
    }
}
