
const fs = require('fs');
const path = require('path');

const REPORT_PATH = path.join(__dirname, 'today_report.md');
console.log('Reading file from:', REPORT_PATH);
console.log('File exists:', fs.existsSync(REPORT_PATH));
if (fs.existsSync(REPORT_PATH)) {
    const content = fs.readFileSync(REPORT_PATH, 'utf8');
    console.log('\n=== File content start ===');
    console.log(content);
    console.log('=== File content end ===\n');
    
    const dateMatch = content.match(/📅\s*(\d+)\s*年\s*(\d+)\s*月\s*(\d+)\s*日/);
    if (dateMatch) {
        const year = parseInt(dateMatch[1]);
        const month = parseInt(dateMatch[2]);
        const day = parseInt(dateMatch[3]);
        const reportDate = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        console.log('Extracted date:', reportDate);
    }
}
