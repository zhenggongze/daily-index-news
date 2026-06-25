const fs = require('fs');
const path = require('path');

const REPORT_PATH = path.join(__dirname, 'today_report.md');
const content = fs.readFileSync(REPORT_PATH, 'utf8');
const lines = content.split('\n');
console.log('=== 前50行内容 ===');
for (let i = 0; i < Math.min(100, lines.length); i++) {
  console.log(i + 1 + ': "' + lines[i] + '"');
}

console.log('\n=== 测试标题匹配 ===');
const VALID_TAGS = ['🟢', '🔴', '⚪'];
const items = [];
let currentTitle = null;
let currentTag = null;
let currentSummary = null;
for (let i = 0; i < lines.length; i++) {
  const line = lines[i];
  const titleMatch = line.match(/\*\*\d️⃣\s*(.+?)\*\*/);
  if (titleMatch) {
    console.log('发现标题行 ' + (i+1) + ': ' + line);
    if (currentTitle && currentSummary) {
      items.push({ title: currentTitle, tag: currentTag, summary: currentSummary.trim() });
    }
    let titleText = titleMatch[1].trim();
    currentTag = null;
    for (const tag of VALID_TAGS) {
      if (titleText.includes(tag)) {
        currentTag = tag;
        titleText = titleText.replace(tag, '').trim();
        break;
      }
    }
    currentTitle = titleText;
    currentSummary = null;
    continue;
  }
  if (currentTitle && !currentSummary && line.match(/^>\s*📌/)) {
    currentSummary = line.replace(/^>\s*📌\s*/, '');
    console.log('发现摘要行 ' + (i+1) + ': ' + line);
    let j = i + 1;
    while (j < lines.length && !lines[j].match(/^---$/) && !lines[j].match(/^\*\*\d️⃣/) && !lines[j].match(/^#/)) {
      currentSummary += ' ' + lines[j].replace(/^>\s*/, '').trim();
      j++;
    }
  }
}
if (currentTitle && currentSummary) {
  items.push({ title: currentTitle, tag: currentTag, summary: currentSummary.trim() });
}
console.log('\n=== 共找到 ' + items.length + ' 条新闻 ===');
for (let k = 0; k < items.length; k++) {
  console.log('第' + (k+1) + '条: ' + items[k].title);
}

console.log('\n=== 测试ETF小节匹配 ===');
function extractCategories(content) {
  const categories = [];
  const lines = content.split('\n');
  for (const line of lines) {
    const etfMatch = line.match(/##\s+.+?ETF\(\d+\)/);
    if (etfMatch) {
      console.log('发现ETF小节: ' + line);
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
const categories = extractCategories(content);
console.log('找到ETF小节: ' + categories);
