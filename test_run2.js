const https = require('https');
const http = require('http');
const dns = require('dns');

dns.setServers(['223.5.5.5', '119.29.29.29', '114.114.114.114']);

function httpGet(url, headers) {
    return new Promise((resolve, reject) => {
        const lib = url.startsWith('https') ? https : http;
        var opts = { timeout: 15000, lookup: function(hostname, opts, cb) {
            dns.resolve4(hostname, function(err, addresses) {
                if (err) { cb(err, null, null); }
                else { cb(null, addresses[0], 4); }
            });
        }};
        if (headers) opts.headers = headers;
        const req = lib.get(url, opts, (res) => {
            if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
                httpGet(res.headers.location, headers).then(resolve).catch(reject);
                return;
            }
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve(data));
        });
        req.on('error', reject);
        req.on('timeout', () => { req.destroy(); reject(new Error('Timeout')); });
    });
}

async function getMarketData() {
    try {
        var data = await httpGet('https://hq.sinajs.cn/list=s_sh000001,s_sh000300,s_sz399006', { 'Referer': 'https://finance.sina.com.cn' });
        if (data === 'Forbidden' || data.indexOf('="') < 0) data = '';
        var lines = data.split('\n');
        var result = {};
        lines.forEach(line => {
            if (line.includes('="')) {
                var match = line.match(/="([^"]+)"/);
                if (match) {
                    var values = match[1].split(',');
                    if (line.includes('sh000001')) result.sh = { price: values[1], change: values[2], percent: values[3] };
                    else if (line.includes('sh000300')) result.hs300 = { price: values[1], change: values[2], percent: values[3] };
                    else if (line.includes('sz399006')) result.cybz = { price: values[1], change: values[2], percent: values[3] };
                }
            }
        });
        return result.sh ? result : null;
    } catch (e) { console.log('市场数据失败: ' + e.message); return null; }
}

async function getNews() {
    var newsSources = [
        { url: 'https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num=50&page=1', cat: 'broad' },
        { url: 'https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num=50&page=2', cat: 'broad' }
    ];
    var allNews = [];
    for (var i = 0; i < newsSources.length; i++) {
        try {
            var data = await httpGet(newsSources[i].url);
            var json = JSON.parse(data);
            if (json.result && json.result.data) {
                json.result.data.forEach(function(item) { item._hintCat = newsSources[i].cat; });
                allNews = allNews.concat(json.result.data);
            }
        } catch (e) { console.log('新闻源失败: ' + e.message); }
    }
    var seen = {};
    var now = Date.now();
    allNews = allNews.filter(function(item) {
        var key = item.title || item.url || '';
        if (seen[key]) return false;
        seen[key] = true;
        if (item.ctime) {
            var newsTime = new Date(item.ctime.replace(/-/g, '/')).getTime();
            if (now - newsTime > 3 * 24 * 3600 * 1000) return false;
        }
        return true;
    });
    return allNews.slice(0, 120);
}

function categorizeNews(newsList) {
    var categories = { broad: [], internet: [], chip: [], medical: [], comm: [] };
    var keywords = {
        broad: ['A股', '上证', '沪深300', '创业板', '科创板', '央行', '逆回购', '外资', 'MSCI', '富时罗素', 'IPO', '退市', '监管', '证监会', '降息', '降准', '加息', 'LPR', 'MLF', '北向资金', '融资融券', '成交额', '财政部', '国务院', '发改委', '商务部', '关税', '特朗普', 'GDP', 'CPI', 'PPI', 'PMI', '通胀', '通缩', '利率', '人民币', '国债', '两融', '注册制', '美联储', '非农', '就业', '失业率', '制裁', '油价', '原油', '黄金', '避险', '美股', '纳斯达克', '标普', '美债', '美元', 'M1', 'M2', '社融', '信贷', '中美关系', '地缘政治', '俄乌', '中东', '指数调整', '纳入指数', '剔除指数', '杠杆资金', '融资余额', '沪港通', '深港通', '港股通', '立案调查', '行政处罚', '新规', '并购重组'],
        internet: ['腾讯', '阿里', '阿里巴巴', '腾讯控股', '京东', '京东集团', '美团', '快手', '拼多多', '百度', '网易', '哔哩哔哩', '小米', '小米集团', '字节跳动', '滴滴', '知乎', '微博', '阅文', '港股互联网', '互联网平台', '电商', '外卖', '本地生活', '在线教育', '社交', '游戏', '短视频', '直播', '云计算', '云服务', '港股通', '恒生科技', '科网', '中概股'],
        chip: ['半导体', '芯片', '集成电路', '晶圆', '光刻', '封装测试', '中芯国际', '韦尔股份', '卓胜微', '闻泰科技', '长电科技', '北方华创', '中微公司', '华虹半导体', '士兰微', '兆易创新', 'AI芯片', '算力芯片', '存储芯片', '先进封装', '半导体设备', '半导体材料', 'EDA', 'GPU', '国产替代', '信创', '南大光电', '安集科技', '江丰电子', '海光信息', '寒武纪', '澜起科技', '拓荆科技', '长川科技', '华海清科', '中科飞测', '芯原股份', '工业富联'],
        medical: ['医药', '医疗', '创新药', '仿制药', '中药', '生物药', '化学药', '医疗器械', '医疗设备', '医疗耗材', '体外诊断', 'IVD', '药明康德', '迈瑞医疗', '恒瑞医药', '爱尔眼科', '智飞生物', '片仔癀', '爱美客', '华熙生物', '泰格医药', '康龙化成', '凯莱英', '集采', '医保谈判', '药品研发', '临床试验', 'CRO', 'CDMO', 'CXO', '医疗服务', '医药零售', '处方药'],
        comm: ['5G', '6G', '通信设备', '光通信', '光模块', '光纤', '数据中心', 'IDC', '云计算基础设施', '物联网', '物联网模组', '运营商', '信创', '国产替代', '紫光国微', '中兴通讯', '光环新网', '移远通信', '信维通信', '亨通光电', '中天科技', '烽火通信', '新易盛', '中际旭创', '天孚通信', '光迅科技']
    };
    var etfMap = { broad: '510300', internet: '513330', chip: '159995', medical: '162412', comm: '515880' };
    var limits = { broad: 8, internet: 5, chip: 5, medical: 5, comm: 5 };
    var industryCats = ['chip', 'comm', 'internet', 'medical'];
    var junkPatterns = ['减持', '折让', '配售', '复牌', '停牌', '联交所最新资料', '每股作价'];
    var nonFinancePatterns = ['自卫队', '台海', '世卫大会', '北约', '太空公司', '航天器', '文身', '布林肯', '中亚五国', '主场外交', '观察者网'];
    var industryExclude = {
        internet: ['恒生科技指数跌', '恒生科技指数涨', '恒指跌', '恒指涨', '指数跌超', '指数涨超', '收跌', '收涨', 'A股收评', '港股收评', '美股收评', '午评', '两融余额', '融资余额', '融券余额', '央行', '降息', '降准', 'LPR', 'MLF', '北向资金', '证监会', '监管新规', '国务院', '财政部', '特朗普', '关税', '中美关系', '战争', '加密隐私', '起诉', '集体上涨', '集体下跌', '股海导航', '隔夜要闻', '高开', '科指涨', '科指跌', '公告与交易提示'],
        chip: ['恒生科技指数跌', '恒生科技指数涨', '指数跌超', '指数涨超', '收跌', '收涨', 'A股收评', '港股收评', '美股收评', '午评', '两融余额', '融资余额', '融券余额', '央行', '降息', '降准', 'LPR', 'MLF', '北向资金', '证监会', '监管新规', '国务院', '财政部', '特朗普', '关税', '中美关系', '战争', '日经指数', '核数师', '委任', '会计师事务所'],
        medical: ['恒生科技指数跌', '恒生科技指数涨', '指数跌超', '指数涨超', '收跌', '收涨', 'A股收评', '港股收评', '午评', '两融余额', '融资余额', '融券余额', '央行', '降息', '降准', 'LPR', 'MLF', '北向资金', '证监会', '监管新规', '国务院', '财政部', '特朗普', '关税', '中美关系', '战争'],
        comm: ['恒生科技指数跌', '恒生科技指数涨', '指数跌超', '指数涨超', '收跌', '收涨', 'A股收评', '港股收评', '午评', '两融余额', '融资余额', '融券余额', '央行', '降息', '降准', 'LPR', 'MLF', '北向资金', '证监会', '监管新规', '国务院', '财政部', '特朗普', '关税', '中美关系', '战争']
    };
    var broadExclude = ['日本', '日经', '日元', '韩国', '韩股', '欧洲', '欧股', '德国', '法国', '英国', '澳洲', '印度', '越南', '新加坡', '泰国', '印尼', '巴西', '高开', '低开', '收盘涨跌', '股市收盘', '拟出售', '附属', '旗下基金', '发布公告', '年度业绩', '股东应占', '溢利', '加工费', '拟购', '拟收购', '拟转让', '作价', '万股', '亿元出售', '涨停', '跌停', '连板', '龙虎榜', '沪指收涨', '沪指收跌', '深证成指收涨', '深证成指收跌', '创业板指收涨', '创业板指收跌', '恒指收涨', '恒指收跌', '恒生科技收涨', '恒生科技收跌', '指数涨超', '指数跌超', '大盘涨', '大盘跌', '全线飘红', '全线飘绿', '集体大涨', '集体大跌', '市场概况', '市场一览', '市场速递', '行情速递', '最新股价', '今日股价', '实时行情', '股票行情', '股价查询', '股票代码', '茅台', '五粮液', '比亚迪', '宁德时代', '腾讯', '阿里', '美团', '中芯国际', '药明康德', '恒瑞医药', '迈瑞医疗', '爱尔眼科', '白酒板块', '半导体板块', '新能源车板块', '医药板块', '医疗板块', '锂电板块', 'A股收评', '港股收评', '美股收评', '午评', '两融余额', '融资余额', '融券余额', '黑色系早报', '工业品早报', '早报', '盘初涨超', '盘初跌超', '早盘涨', '早盘跌', '科伦博泰', '首挂上市', '首日高开', '首日涨'];
    var used = {};
    var debugLog = [];
    newsList.forEach(function(news) {
        var title = (news.title || '') + (news.intro || '') + (news.wap_intro || '');
        var newsKey = news.title || news.url || '';
        if (used[newsKey]) return;
        var isJunk = junkPatterns.some(function(p) { return title.includes(p); });
        if (isJunk) { debugLog.push('[JUNK] ' + news.title); return; }
        var isNonFinance = nonFinancePatterns.some(function(p) { return title.includes(p); });
        if (isNonFinance) { debugLog.push('[NONFIN] ' + news.title); return; }
        var matched = null;
        for (var ci = 0; ci < industryCats.length; ci++) {
            var cat = industryCats[ci];
            var matchedKw = keywords[cat].filter(function(k) { return title.includes(k); });
            if (matchedKw.length > 0) {
                var isExcluded = industryExclude[cat] && industryExclude[cat].some(function(p) { return title.includes(p); });
                if (!isExcluded) {
                    matched = cat;
                    debugLog.push('[MATCH:' + cat + '] ' + news.title + ' (kw:' + matchedKw.join(',') + ')');
                    break;
                } else {
                    debugLog.push('[EXCL:' + cat + '] ' + news.title + ' (kw:' + matchedKw.join(',') + ')');
                }
            }
        }
        if (!matched && keywords.broad.some(function(k) { return title.includes(k); })) {
            var matchedBroadKw = keywords.broad.filter(function(k) { return title.includes(k); });
            var isBroadExcluded = broadExclude.some(function(p) { return title.includes(p); });
            if (!isBroadExcluded) {
                matched = 'broad';
                debugLog.push('[MATCH:broad] ' + news.title + ' (kw:' + matchedBroadKw.join(',') + ')');
            } else {
                debugLog.push('[EXCL:broad] ' + news.title + ' (kw:' + matchedBroadKw.join(',') + ')');
            }
        }
        if (!matched) { debugLog.push('[DROP] ' + news.title); return; }
        if (categories[matched].length < limits[matched]) {
            categories[matched].push({
                t: news.title || '暂无标题',
                i: '🟡',
                e: etfMap[matched],
                r: 0,
                b: news.intro || news.wap_intro || news.summary || '暂无摘要',
                url: news.url || news.wap_url || '#'
            });
            used[newsKey] = true;
        } else {
            debugLog.push('[FULL:' + matched + '] ' + news.title);
        }
    });
    return { categories: categories, debug: debugLog };
}

async function main() {
    console.log('=== 获取市场数据 ===');
    var market = await getMarketData();
    if (market) {
        console.log('上证: ' + market.sh.price + ' ' + market.sh.percent + '%');
        console.log('沪深300: ' + market.hs300.price + ' ' + market.hs300.percent + '%');
        console.log('创业板: ' + market.cybz.price + ' ' + market.cybz.percent + '%');
    } else {
        console.log('市场数据获取失败');
    }

    console.log('\n=== 获取新闻 ===');
    var newsList = await getNews();
    console.log('获取到 ' + newsList.length + ' 条新闻');

    console.log('\n=== 分类调试日志 ===');
    var result = categorizeNews(newsList);
    result.debug.forEach(function(line) { console.log(line); });

    console.log('\n=== 分类结果 ===');
    var catNames = { broad: '宽基', internet: '互联网', chip: '芯片', medical: '医疗', comm: '通信' };
    for (var cat in catNames) {
        console.log('\n--- ' + catNames[cat] + ' (' + result.categories[cat].length + '条) ---');
        result.categories[cat].forEach(function(item, idx) {
            console.log((idx + 1) + '. ' + item.t);
            console.log('   摘要: ' + (item.b.length > 100 ? item.b.substring(0, 100) + '...' : item.b));
        });
    }
}

main().catch(console.error);
