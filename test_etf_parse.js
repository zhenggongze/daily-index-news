
const fs = require('fs');
const path = require('path');
const REPORT_PATH = path.join(__dirname, 'today_report.md');
const content = fs.readFileSync(REPORT_PATH, 'utf8');

function extractCategories(content) {
  const categories = [];
  const lines = content.split('\n');
  for (let i=0;i<lines.length;i++) {
    const line=lines[i];
    console.log(`Line ${i}: ${JSON.stringify(line.substring(0,60))}`);
    const etfMatch = line.match(/##\s+.+?ETF\(\d+\)/);
    if (etfMatch) {
      console.log('✓ 发现匹配:', etfMatch[0]);
      const etfIndex = line.indexOf('ETF');
      let start = line.indexOf('##') + 2;
      for (let c = start; c < line.length; c++) {
        if (line[c] !== ' ' && !/[\u{1F300}-\u{1F9FF}]/u.test(line[c])) {
          start = c;
          break;
        }
      }
      const name = line.substring(start, etfIndex).replace(/[^\u4e00-\u9fa5a-zA-Z0-9]/g, '').trim();
      if (name) {
        categories.push(name + 'ETF');
      }
    }
  }
  return categories;
}

const cats = extractCategories(content);
console.log('\n找到的ETF小节:', cats);
