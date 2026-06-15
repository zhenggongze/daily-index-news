const fs = require('fs');
const path = require('path');
const config = require('./config.json');
const { getShanghaiDate, logExecution } = require('./utils');

const REPORT_PATH = path.join(__dirname, 'today_report.md');
const LOG_PATH = path.join(__dirname, 'push_log.json');

const TAG_GREEN = '\u{1F7E2}';
const TAG_RED = '\u{1F534}';
const TAG_WHITE = '\u26AA';
const VALID_TAGS = [TAG_GREEN, TAG_RED, TAG_WHITE];
const REQUIRED_SECTIONS = config.requiredSections || ['恒生互联网ETF', '芯片ETF', '医疗ETF', '通信ETF'];

const MIN_SUMMARY_LENGTH = 80;
const MIN_DATA_POINTS = 2;
const MAX_GREEN_PCT = 65;
const MIN_RED_PCT = 5;
const MIN_INDUSTRY_LEVEL_NEWS = 2;
const HISTORY_SIM_THRESHOLD = 0.50;
const INTERNAL_DUP_THRESHOLD = 0.60;

const INDUSTRY_KEYWORDS = [
    '行业趋势', '景气度', '产业链', '渗透率', '全球化', '出海',
    '技术路线', '标准发布', '法规落地', '监管', '关税', '制裁',
    '贸易', '政策', '供需', '竞争格局', '市场份额', '产业升级',
    '量产', '商业化', '研发投入', '创新转型', '技术路径',
    '替代', '降本', '涨价', '降价', '成本',
    '市场空间', '增长潜力', '周期', '拐点', '出清',
    '全球', '国内', '海外', '出口', '进口', '外需',
    '商业化落地', '规模回报', '集中度', '分化', '龙头'
];

const STOCK_NAMES = [
    '茅台', '五粮液', '泸州老窖', '汾酒', '洋河', '古井贡酒', '舍得', '酒鬼酒',
    '比亚迪', '宁德时代', '特斯拉', '蔚来', '小鹏', '理想', '小米', '华为',
    '腾讯', '阿里', '京东', '美团', '拼多多', '百度', '网易', '快手',
    '恒瑞', '百济神州', '药明康德', '信达生物', '荣昌生物', '凯莱英', '康龙化成',
    '中芯国际', '北方华创', '中微公司', '海光信息', '长鑫科技', '英伟达', 'AMD',
    '立讯精密', '工业富联', '华天科技', '韦尔股份', '兆易创新',
    '迈瑞医疗', '联影医疗', '爱尔眼科', '泰格医药',
    '汇川技术', '三花智控', '华友钴业', '赣锋锂业', '天齐锂业',
    '华润', '万科', '保利', '招商蛇口', '中国平安', '招商银行', '工商银行',
    '中信证券', '中金公司', '华泰证券', '国泰君安',
    '南大光电', '安集科技', '江丰电子', '寒武纪', '澜起科技',
    '拓荆科技', '长川科技', '华海清科', '中科飞测', '芯原股份',
    '亨通光电', '中天科技', '烽火通信', '新易盛', '中际旭创', '天孚通信', '光迅科技'
];

const VAGUE_PHRASES = [
    '或将', '有望', '值得关注', '值得期待', '持续关注', '密切跟踪',
    '影响较大', '影响显著', '市场分析认为', '业内人士认为',
    '或将受益', '或将承压', '逐步恢复', '稳步推进',
    '积极信号', '不确定性', '有待观察', '有目共睹'
];

const PROFESSIONAL_TERMS = [
    '逆回购操作', '买断式逆回购', 'SLF', 'PSL',
    '场外期权', '净资本', '国债期货', '利率互换', '信用违约互换', 'CDS',
    '做市商', '转融通', '融券', '股票质押', '大宗交易', '协议转让',
    '券商门槛', '期货公司', '基金销售渠道', '资管新规'
];

const SEMI_PROFESSIONAL_TERMS = [
    'MLF', '中期借贷资金', '降准降息', '量化宽松', '缩表',
    '存款准备金率', 'LPR下调', '麻辣粉', '酸辣粉', '特麻辣粉'
];

const SECTOR_PATTERNS = [
    /半导体板块/, /医药板块/, /白酒板块/, /新能源板块/, /消费板块/,
    /科技板块/, /互联网板块/, /银行板块/, /地产板块/, /券商板块/,
    /行业涨跌/, /行业指数/, /板块估值/, /板块涨跌/, /行业估值/
];

// ============================================================
// 工具函数
// ============================================================

function readReport() {
    if (!fs.existsSync(REPORT_PATH)) return null;
    return fs.readFileSync(REPORT_PATH, 'utf8');
}

function extractNewsItems(content) {
    const items = [];
    const lines = content.split('\n');
    let currentTitle = null;
    let currentTag = null;
    let currentSummary = null;
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const titleMatch = line.match(/\*\*\d️⃣\s*(.+?)\*\*/);
        if (titleMatch) {
            if (currentTitle && currentSummary) {
                items.push({ title: currentTitle, tag: currentTag, summary: currentSummary.trim(), summaryStartLine: -1 });
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
        if (currentTitle && !currentSummary && line.match(/^>\s*/)) {
            currentSummary = line.replace(/^>\s*/, '');
            let j = i + 1;
            while (j < lines.length && !lines[j].match(/^---$/) && !lines[j].match(/^\*\*\d️⃣/) && !lines[j].match(/^#/)) {
                currentSummary += ' ' + lines[j].replace(/^>\s*/, '').trim();
                j++;
            }
        }
    }
    if (currentTitle && currentSummary) {
        items.push({ title: currentTitle, tag: currentTag, summary: currentSummary.trim(), summaryStartLine: -1 });
    }
    return items;
}

function extractCategories(content) {
    const categories = [];
    const lines = content.split('\n');
    for (const line of lines) {
        const etfMatch = line.match(/##\s+.+?ETF\(\d+\)/);
        if (etfMatch) {
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

function jaccardSimilarity(a, b) {
    const setA = new Set(a.split(''));
    const setB = new Set(b.split(''));
    const intersection = new Set([...setA].filter(x => setB.has(x)));
    const union = new Set([...setA, ...setB]);
    return union.size === 0 ? 0 : intersection.size / union.size;
}

function semanticSimilarity(a, b) {
    const cleanA = a.replace(/[^\u4e00-\u9fa5a-zA-Z0-9]/g, '');
    const cleanB = b.replace(/[^\u4e00-\u9fa5a-zA-Z0-9]/g, '');
    if (cleanA.length === 0 || cleanB.length === 0) return 0;
    const minLen = Math.min(cleanA.length, cleanB.length);
    let lcsLen = findLCS(cleanA, cleanB);
    const lcsRatioShort = lcsLen / minLen;
    const lcsRatioAvg = (2 * lcsLen) / (cleanA.length + cleanB.length);
    let totalShared = 0;
    let remA = cleanA;
    let remB = cleanB;
    for (let round = 0; round < 5; round++) {
        const lcs = findLCSstr(remA, remB);
        if (lcs.length < 2) break;
        totalShared += lcs.length;
        remA = remA.replace(lcs, '');
        remB = remB.replace(lcs, '');
    }
    const coverageA = totalShared / cleanA.length;
    const coverageB = totalShared / cleanB.length;
    const maxCoverage = Math.max(coverageA, coverageB);
    return lcsRatioShort * 0.35 + lcsRatioAvg * 0.15 + maxCoverage * 0.5;
}

function findLCS(a, b) {
    const m = a.length, n = b.length;
    const dp = new Array(m + 1);
    for (let i = 0; i <= m; i++) dp[i] = new Array(n + 1).fill(0);
    let maxLen = 0;
    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (a[i - 1] === b[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
                if (dp[i][j] > maxLen) maxLen = dp[i][j];
            }
        }
    }
    return maxLen;
}

function findLCSstr(a, b) {
    const m = a.length, n = b.length;
    const dp = new Array(m + 1);
    for (let i = 0; i <= m; i++) dp[i] = new Array(n + 1).fill(0);
    let maxLen = 0, endIdx = 0;
    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (a[i - 1] === b[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
                if (dp[i][j] > maxLen) {
                    maxLen = dp[i][j];
                    endIdx = i;
                }
            }
        }
    }
    return a.substring(endIdx - maxLen, endIdx);
}

function getETFSectionRegexes() {
    return [
        { regex: /##\s*芯片ETF\((\d+)\)([\s\S]*?)(?=##\s*通信ETF|##\s*恒生互联网ETF|##\s*医疗ETF|##\s*⚠️|#\s|$)/, code: '159995' },
        { regex: /##\s*通信ETF\((\d+)\)([\s\S]*?)(?=##\s*恒生互联网ETF|##\s*医疗ETF|##\s*⚠️|#\s|$)/, code: '515880' },
        { regex: /##\s*恒生互联网ETF\((\d+)\)([\s\S]*?)(?=##\s*医疗ETF|##\s*⚠️|#\s|$)/, code: '159688' },
        { regex: /##\s*医疗ETF\((\d+)\)([\s\S]*?)(?=##\s*⚠️|#\s|$)/, code: '512170' }
    ];
}

// ============================================================
// 校验函数（全部返回 hardErrors）
// ============================================================

function checkContentExists(content) {
    const errors = [];
    if (!content) errors.push('❌ today_report.md 文件不存在');
    else if (content.length < 150) errors.push(`❌ 日报内容过短(${content.length}字符)，可能为空`);
    return errors;
}

function checkTimeliness(content) {
    const errors = [];
    const today = getShanghaiDate();
    const dateMatch = content.match(/📅\s*(\d{4})年(\d{1,2})月(\d{1,2})日/);
    if (!dateMatch) {
        errors.push('❌ 未找到日期行（📅 YYYY年M月D日格式）');
        return errors;
    }
    const reportDate = `${dateMatch[1]}-${String(dateMatch[2]).padStart(2, '0')}-${String(dateMatch[3]).padStart(2, '0')}`;
    if (reportDate !== today) {
        errors.push(`❌ 日报日期${reportDate}与今天${today}不匹配，禁止推送隔日报`);
    }
    return errors;
}

function checkSectionCompleteness(content) {
    const errors = [];
    const foundSections = extractCategories(content);
    for (const required of REQUIRED_SECTIONS) {
        const found = foundSections.some(s => s.includes(required));
        if (!found) {
            errors.push(`❌ 缺少必需的小节: ${required}，必须在##小节标题中出现`);
        }
    }
    return errors;
}

function checkFormat(content) {
    const errors = [];
    const lines = content.split('\n');
    const newsItems = extractNewsItems(content);

    // 一级标题检查
    const sectionHeadings = lines.filter(l => l.match(/^#\s+[^#]/));
    const h1Headings = sectionHeadings.map(l => l.trim());
    if (!h1Headings.some(h => h.includes('宽基'))) {
        errors.push('❌ 宽基资讯必须使用#一级标题（例如"# 📈 宽基指数重要资讯"）');
    }
    if (!h1Headings.some(h => h.includes('行业'))) {
        errors.push('❌ 行业资讯必须使用#一级标题（例如"# 🏭 行业指数重要资讯"）');
    }

    // 新闻格式检查
    for (let i = 0; i < newsItems.length; i++) {
        const item = newsItems[i];
        if (!VALID_TAGS.includes(item.tag)) {
            errors.push(`❌ 第${i+1}条"${item.title.slice(0,20)}..."标签无效("${item.tag}")，必须为🟢/🔴/⚪之一`);
        }
        if (item.summary.includes('**')) {
            errors.push(`❌ 第${i+1}条"${item.title.slice(0,20)}..."摘要含加粗标记（**），摘要中不可用Markdown加粗`);
        }
    }

    // 标题后空行检查
    for (let li = 0; li < lines.length; li++) {
        const line = lines[li];
        if (line.match(/\*\*\d️⃣/) && line.match(/\*\*$/)) {
            let foundBlank = false;
            for (let k = li + 1; k < Math.min(li + 4, lines.length); k++) {
                if (lines[k].trim() === '') { foundBlank = true; break; }
                if (lines[k].match(/^>\s*/)) break;
            }
            if (!foundBlank) {
                errors.push(`❌ 第${li+1}行标题"${line.slice(0,30)}..."后缺少空行（标题和摘要之间需空一行）`);
            }
        }
    }

    // 摘要>引用格式检查
    for (let li = 0; li < lines.length; li++) {
        const line = lines[li];
        if (line.match(/^\*\*\d️⃣/) && line.match(/🔴|🟢|⚪.*\*\*$/)) {
            let nextLine = '';
            for (let k = li + 1; k < Math.min(li + 5, lines.length); k++) {
                if (lines[k].trim() !== '') { nextLine = lines[k].trim(); break; }
            }
            if (nextLine && !nextLine.startsWith('>')) {
                errors.push(`❌ 第${li+1}行标题的摘要未使用>块引用格式（须以"> "开头）`);
            }
        }
    }

    // push_single推送类型检查
    const pushScript = fs.readFileSync(path.join(__dirname, 'push_single.js'), 'utf8');
    if (!pushScript.includes("'markdown'") && !pushScript.includes('"markdown"')) {
        errors.push('❌ push_single.js 推送类型不是markdown');
    }

    return errors;
}

function checkSummaryQuality(content) {
    const errors = [];
    const items = extractNewsItems(content);
    const dataPattern = /\d+\.?\d*(%|亿|万|元|美元|点|倍|bp|基点|个百分点|桶|吨)/g;
    const logicPattern = /利好|利空|承压|受益|压制|支撑|修复|出清|拐点|配置|关注|警惕|风险|担忧|聚焦|看好|看空|回暖|降温|反弹|回调|上行|下行|高|低|强|弱|增|减/;

    for (let i = 0; i < items.length; i++) {
        const item = items[i];
        const summary = item.summary;

        // 1. 摘要最低长度
        if (summary.length < MIN_SUMMARY_LENGTH) {
            errors.push(`❌ 第${i+1}条"${item.title.slice(0,20)}..."摘要仅${summary.length}字，低于最低要求${MIN_SUMMARY_LENGTH}字`);
        }

        // 2. 数据密度
        const matches = summary.match(dataPattern);
        const dataCount = matches ? matches.length : 0;
        if (dataCount < MIN_DATA_POINTS) {
            errors.push(`❌ 第${i+1}条"${item.title.slice(0,20)}..."摘要仅${dataCount}个数据点（数字+单位），需要≥${MIN_DATA_POINTS}个`);
        }

        // 3. 投资逻辑判断（软检查，不阻断）
        // 硬编码关键词匹配有限，有"营收增长""净利润下降"等明显信号也算有逻辑
        // 本检查保留但结果并入软警告

        // 4. 摘要不能直接复制或重新表述标题内容
        const titleClean = item.title.replace(/[\s,，。、：:；;！!？?🟢🔴⚪⚠️]/g, '');
        const summaryClean = summary.replace(/[\s,，。、：:；;！!？?🟢🔴⚪⚠️]/g, '');
        if (summaryClean.includes(titleClean) && titleClean.length > 4) {
            errors.push(`❌ 第${i+1}条"${item.title.slice(0,20)}..."摘要直接复制了标题原文，摘要应独立展开信息`);
        }

        // 5. 摘要不能仅重新表述标题内容（用新词说同一件事）
        // 将标题中连续2字以上的内容片段从摘要中移除，检查剩余信息量
        const titleBigrams = [];
        for (let ti = 0; ti < titleClean.length - 1; ti++) {
            const bigram = titleClean.substring(ti, ti + 3);
            if (bigram.length >= 2) titleBigrams.push(bigram);
        }
        let remainingSummary = summaryClean;
        for (const bigram of titleBigrams) {
            remainingSummary = remainingSummary.replace(bigram, '');
        }
        remainingSummary = remainingSummary.replace(/\s+/g, '').trim();
        const remainingRatio = remainingSummary.length / Math.max(summaryClean.length, 1);
        if (remainingRatio < 0.50) {
            errors.push(`❌ 第${i+1}条"${item.title.slice(0,20)}..."摘要仅${remainingSummary.length}字与标题不同（剩余${(remainingRatio*100).toFixed(0)}%），摘要不能重新表述标题内容，须提供标题之外的新信息`);
        }

        // 6. 空泛表述不能过多
        let vagueCount = 0;
        for (const phrase of VAGUE_PHRASES) {
            if (summary.includes(phrase)) vagueCount++;
        }
        if (vagueCount >= 3) {
            errors.push(`❌ 第${i+1}条"${item.title.slice(0,20)}..."摘要含${vagueCount}处空泛表述（或将/有望/值得关注等），缺乏具体信息`);
        }
    }
    return errors;
}

function checkInternalDedup(content) {
    const errors = [];
    const items = extractNewsItems(content);
    for (let i = 0; i < items.length; i++) {
        for (let j = i + 1; j < items.length; j++) {
            const sim = jaccardSimilarity(items[i].title, items[j].title);
            if (sim > INTERNAL_DUP_THRESHOLD) {
                errors.push(`❌ 标题高度重复(相似度${(sim*100).toFixed(0)}%):\n  "${items[i].title.slice(0,30)}..."\n  "${items[j].title.slice(0,30)}..."`);
            }
        }
    }
    return errors;
}

function checkHistoryDup(content) {
    const errors = [];
    const historyPath = path.join(__dirname, 'news_history.json');
    if (!fs.existsSync(historyPath)) return errors;

    let history;
    try {
        history = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
    } catch (e) {
        return errors;
    }

    const today = new Date();
    const recentTitles = [];
    for (let d = 1; d <= 3; d++) {
        const past = new Date(today);
        past.setDate(past.getDate() - d);
        const key = `${past.getFullYear()}-${String(past.getMonth()+1).padStart(2,'0')}-${String(past.getDate()).padStart(2,'0')}`;
        if (history[key]) recentTitles.push(...history[key]);
    }
    if (recentTitles.length === 0) return errors;

    const items = extractNewsItems(content);
    for (const item of items) {
        let maxSim = 0;
        let matchedHistory = '';
        for (const histTitle of recentTitles) {
            // 使用摘要与历史标题比较，摘要含具体数据更能反映真实重复
            const sim = semanticSimilarity(item.summary, histTitle);
            if (sim > maxSim) { maxSim = sim; matchedHistory = histTitle; }
        }
        if (maxSim > HISTORY_SIM_THRESHOLD) {
            errors.push(`❌ 与近3天新闻高度重复(相似度${(maxSim*100).toFixed(0)}%): "${item.title.slice(0,25)}..." ≈ "${matchedHistory.slice(0,25)}..."`);
        }
    }
    return errors;
}

function checkBroadBaseQuality(content) {
    const errors = [];
    const broadMatch = content.match(/# 📈 宽基指数重要资讯[\s\S]*?(?=# 🏭 行业指数重要资讯)/);
    if (!broadMatch) return errors;

    const broadSection = broadMatch[0];
    const lines = broadSection.split('\n');
    let newsIndex = 0;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (!line.match(/^\*\*\d️⃣/)) continue;
        newsIndex++;
        const title = line;
        let summary = '';
        for (let j = i + 1; j < Math.min(i + 10, lines.length); j++) {
            if (lines[j].match(/^>\s*/)) { summary = lines[j]; break; }
        }
        const fullText = title + ' ' + summary;

        // 禁止个股
        for (const stock of STOCK_NAMES) {
            if (fullText.includes(stock)) {
                errors.push(`❌ 宽基资讯第${newsIndex}条含个股"${stock}"，宽基只关注宏观政策，不出现个股名称`);
                break;
            }
        }

        // 禁止专业金融术语
        for (const term of PROFESSIONAL_TERMS) {
            if (fullText.includes(term)) {
                errors.push(`❌ 宽基资讯第${newsIndex}条含专业术语"${term}"，ETF投资者看不懂，请用通俗语言改写`);
                break;
            }
        }

        // 禁止行业板块数据
        for (const pat of SECTOR_PATTERNS) {
            if (pat.test(fullText)) {
                errors.push(`❌ 宽基资讯第${newsIndex}条含行业板块内容"${fullText.match(pat)[0]}"，应归入行业ETF小节`);
                break;
            }
        }
    }
    return errors;
}

function checkMarketDataInNews(content) {
    const errors = [];
    const broadMatch = content.match(/# 📈 宽基指数重要资讯[\s\S]*?(?=# 🏭 行业指数重要资讯)/);
    if (!broadMatch) return errors;

    const lines = broadMatch[0].split('\n');
    let newsIndex = 0;
    const titlePatterns = [
        { regex: /\d+股.*(上涨|下跌|飘红|飘绿)/, desc: '涨跌家数统计' },
        { regex: /\d+家.*(上涨|下跌)/, desc: '涨跌家数统计' },
        { regex: /涨跌(幅|比|家数)/, desc: '涨跌统计' },
        { regex: /(逼近|触及|失守|站上|突破)\s*\d{3,}\s*(点|关口)/, desc: '指数点位描述' },
        { regex: /(急跌|急涨|暴涨|暴跌|大涨|大跌).*(指数|大盘|A股)/, desc: '盘面涨跌描述' },
        { regex: /(指数|大盘|A股).*(急跌|急涨|暴涨|暴跌|大涨|大跌)/, desc: '盘面涨跌描述' },
        { regex: /成交(额|量).*(万亿|天量|地量|缩量|放量)/, desc: '成交额数据' },
        { regex: /(万亿|千亿).*(成交|换手|放量)/, desc: '成交额数据' },
        { regex: /(涨停|跌停)\s*\d+\s*(家|只|股)/, desc: '涨跌停统计' },
        { regex: /换手率/, desc: '换手率数据' }
    ];

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (!line.match(/^\*\*\d️⃣/)) continue;
        newsIndex++;
        const titleText = line.replace(/\*\*\d️⃣\s*/, '').replace(/\*\*$/, '').replace(/\s*(🟢|🔴|⚪)\s*\*?\*?$/, '').trim();
        for (const pat of titlePatterns) {
            if (pat.regex.test(titleText)) {
                errors.push(`❌ 宽基资讯第${newsIndex}条是盘面数据而非新闻(${pat.desc})，用户每天盯盘不需要此类信息`);
                break;
            }
        }
    }
    return errors;
}

function checkNoIconInSummary(content) {
    const errors = [];
    const items = extractNewsItems(content);
    const iconPattern = /^[\u{1F300}-\u{1F9FF}\u{2600}-\u{27BF}]/u;

    for (let i = 0; i < items.length; i++) {
        const firstChar = items[i].summary.trim().charAt(0);
        if (iconPattern.test(firstChar)) {
            errors.push(`❌ 第${i+1}条"${items[i].title.slice(0,20)}..."摘要以icon(${firstChar})开头，摘要直接输出文字不加icon`);
        }
    }
    return errors;
}

function checkLogicJudgmentSoft(content) {
    const warnings = [];
    const items = extractNewsItems(content);
    const logicPattern = /利好|利空|承压|受益|压制|支撑|修复|出清|拐点|配置|关注|警惕|风险|担忧|聚焦|看好|看空|回暖|降温|反弹|回调|上行|下行|高|低|强|弱|增|减|拖累|加剧|提振|分化|博弈|承压|回暖|降温|出清|企稳|修复|释放|收缩|扩张/;

    for (let i = 0; i < items.length; i++) {
        if (!logicPattern.test(items[i].summary)) {
            warnings.push(`⚠️ 第${i+1}条"${items[i].title.slice(0,20)}..."摘要缺少投资逻辑判断（利好/利空/承压/支撑等），建议补充`);
        }
    }
    return warnings;
}

function checkTagDistribution(content) {
    const errors = [];
    const items = extractNewsItems(content);
    const total = items.length;
    if (total < 10) return errors;

    let green = 0, red = 0, white = 0;
    for (const item of items) {
        if (item.tag === '🟢') green++;
        else if (item.tag === '🔴') red++;
        else if (item.tag === '⚪') white++;
    }
    const greenPct = Math.round(green / total * 100);
    const redPct = Math.round(red / total * 100);
    const whitePct = Math.round(white / total * 100);

    if (greenPct > MAX_GREEN_PCT) {
        errors.push(`❌ 利好(${TAG_GREEN})占比${greenPct}%(${green}条)，超过上限${MAX_GREEN_PCT}%。请增加利空(${TAG_RED})或中性(${TAG_WHITE})新闻`);
    }
    if (redPct < MIN_RED_PCT && total >= 20) {
        errors.push(`❌ 利空(${TAG_RED})仅${red}条(${redPct}%)，低于最低要求${MIN_RED_PCT}%。必须包含风险/承压类新闻`);
    }
    return errors;
}

function checkIndustryStockNames(content) {
    const errors = [];
    let holdings = null;
    try {
        holdings = JSON.parse(fs.readFileSync(path.join(__dirname, 'etf_holdings.json'), 'utf8'));
    } catch (e) {
        errors.push('❌ etf_holdings.json不存在，无法校验行业个股是否在前5大持仓内');
        return errors;
    }

    const etfSections = getETFSectionRegexes();
    for (const section of etfSections) {
        const match = content.match(section.regex);
        if (!match) continue;
        const sectionContent = match[2];
        const top5 = holdings.holdings[section.code] ? holdings.holdings[section.code].top5 : [];
        const newsMatches = sectionContent.match(/\*\*\d️⃣\s*(.+?)\*\*/g) || [];
        for (const newsLine of newsMatches) {
            const titleMatch = newsLine.match(/\*\*\d️⃣\s*(.+?)\*\*/);
            if (!titleMatch) continue;
            const title = titleMatch[1];
            for (const stock of STOCK_NAMES) {
                if (title.includes(stock)) {
                    const inTop5 = top5.some(t => t.includes(stock) || stock.includes(t));
                    if (!inTop5) {
                        errors.push(`❌ ${holdings.holdings[section.code].name}含非前5大持仓个股"${stock}"，只允许top5持仓个股的新闻: "${title.slice(0,30)}..."`);
                    }
                    break;
                }
            }
        }
    }
    return errors;
}

function checkIndustryLevelNews(content) {
    const errors = [];
    const etfSections = getETFSectionRegexes();
    const allItems = extractNewsItems(content);

    for (const section of etfSections) {
        const match = content.match(section.regex);
        if (!match) continue;
        const sectionContent = match[2];
        const etfName = match[0].match(/##\s*(.+?)\(/);
        const name = etfName ? etfName[1] : 'unknown';

        // Find items belonging to this section
        const sectionItems = allItems.filter(item => sectionContent.includes(item.title.slice(0, 15)));

        let industryCount = 0;
        for (const item of sectionItems) {
            const hasIndustryKeyword = INDUSTRY_KEYWORDS.some(kw => item.summary.includes(kw));
            if (hasIndustryKeyword) industryCount++;
        }

        if (industryCount < MIN_INDUSTRY_LEVEL_NEWS) {
            errors.push(`❌ ${name}行业级别新闻仅${industryCount}条（摘要含行业关键词），需要≥${MIN_INDUSTRY_LEVEL_NEWS}条`);
        }
    }
    return errors;
}

function checkTencentAlibabaBuybackPriority(content) {
    const errors = [];
    const internetSection = content.match(/##\s*恒生互联网ETF\((\d+)\)([\s\S]*?)(?=##\s|#\s|$)/);
    if (!internetSection) return errors;

    const sectionContent = internetSection[2];
    const items = extractNewsItems(sectionContent);
    if (items.length === 0) return errors;

    const buybackKeywords = ['回购', '增持', '股份', '买回'];
    const buybackStocks = ['腾讯', '阿里巴巴', '阿里'];
    let hasBuybackNews = false;

    for (const item of items) {
        const hasStock = buybackStocks.some(s => item.title.includes(s));
        const hasKeyword = buybackKeywords.some(k => item.summary.includes(k) || item.title.includes(k));
        if (hasStock && hasKeyword) {
            hasBuybackNews = true;
            break;
        }
    }

    // Check if first item is a buyback news
    const firstItem = items[0];
    const firstIsBuyback = buybackStocks.some(s => firstItem.title.includes(s)) &&
        buybackKeywords.some(k => firstItem.summary.includes(k) || firstItem.title.includes(k));

    if (hasBuybackNews && !firstIsBuyback) {
        errors.push('❌ 恒生互联网ETF含腾讯/阿里回购新闻但未排在第1条，回购新闻须优先于其他新闻');
    }
    return errors;
}

// ============================================================
// 主入口
// ============================================================

function runAllChecks() {
    logExecution(LOG_PATH, 'validate_report', 'started');

    const content = readReport();
    let allErrors = [];
    let allWarnings = [];

    // 1. 文件存在性
    allErrors.push(...checkContentExists(content));
    if (allErrors.length > 0) {
        const result = { pass: false, hardErrors: allErrors, hardErrorCount: allErrors.length, softWarnings: [], softWarningCount: 0, newsCount: 0, canFallbackPush: false, severity: 'error' };
        console.log(JSON.stringify(result, null, 2));
        process.exit(1);
    }

    // 2. 日期校验
    allErrors.push(...checkTimeliness(content));

    // 3. 小节完整性
    allErrors.push(...checkSectionCompleteness(content));

    // 4. 格式校验
    allErrors.push(...checkFormat(content));

    // 5. 内部去重
    allErrors.push(...checkInternalDedup(content));

    // 6. 历史去重（摘要 vs 历史标题，阈值50%）
    allErrors.push(...checkHistoryDup(content));

    // 7. 摘要质量（长度/数据密度/独创性—硬；投资逻辑—软）
    allErrors.push(...checkSummaryQuality(content));
    allWarnings.push(...checkLogicJudgmentSoft(content));

    // 8. 宽基质量（个股/专业术语/板块数据/盘面数据）
    allErrors.push(...checkBroadBaseQuality(content));
    allErrors.push(...checkMarketDataInNews(content));

    // 9. 摘要icon检查（硬—摘要不能以icon开头）
    allErrors.push(...checkNoIconInSummary(content));

    // 10. 标签分布（利好上限/利空下限）
    allErrors.push(...checkTagDistribution(content));

    // 11. 行业个股检查（前5大持仓）
    allErrors.push(...checkIndustryStockNames(content));

    // 12. 行业级别新闻数量（按摘要行业关键词检测）
    allErrors.push(...checkIndustryLevelNews(content));

    // 13. 恒生互联网ETF回购排序（有腾讯/阿里回购则必须在第1条）
    allErrors.push(...checkTencentAlibabaBuybackPriority(content));

    const newsItems = extractNewsItems(content);
    const result = {
        pass: allErrors.length === 0,
        hardErrors: allErrors,
        hardErrorCount: allErrors.length,
        softWarnings: allWarnings,
        softWarningCount: allWarnings.length,
        newsCount: newsItems.length,
        canFallbackPush: newsItems.length >= 20,
        severity: allErrors.length === 0 ? (allWarnings.length === 0 ? 'clean' : 'warning') : 'error'
    };

    console.log(JSON.stringify(result, null, 2));

    if (allErrors.length > 0) {
        logExecution(LOG_PATH, 'validate_report', 'failed', `hardErrors:${allErrors.length} softWarnings:${allWarnings.length}`);
        process.exit(1);
    } else {
        logExecution(LOG_PATH, 'validate_report', 'success', `softWarnings:${allWarnings.length}`);
    }
}

runAllChecks();
