var testCases = [
    { title: '腾讯Q1营收1964亿同比增9%，AI资本开支付款370亿', expect: 'internet', reason: '腾讯=恒生互联网' },
    { title: '阿里巴巴云AI收入占比首破30%，外部商业化收入增40%', expect: 'internet', reason: '阿里=恒生互联网' },
    { title: '京东Q1营收3157亿，年活跃用户超7.4亿', expect: 'internet', reason: '京东=恒生互联网' },
    { title: '快手电商GMV突破万亿，直播带货增速放缓', expect: 'internet', reason: '快手=恒生互联网' },
    { title: '港股互联网板块集体上涨，恒生科技指数涨2%', expect: null, reason: '纯行情涨跌，行业排除' },
    { title: '中芯国际Q1营收176亿+8.1%，成熟制程重获定价权', expect: 'chip', reason: '中芯国际=芯片' },
    { title: '国产AI芯片加速替代，英伟达在华份额归零', expect: 'chip', reason: '芯片/AI=芯片' },
    { title: '北方华创获大基金增持，半导体设备订单暴增', expect: 'chip', reason: '北方华创/半导体=芯片' },
    { title: '存储芯片价格持续上涨，DRAM累计涨幅达45%', expect: 'chip', reason: '存储芯片=芯片' },
    { title: '创新药数据保护新规落地，估值逻辑转向研发价值', expect: 'medical', reason: '创新药=医疗' },
    { title: '恒瑞医药Q1净利润同比增30%，创新药收入占比60%', expect: 'medical', reason: '恒瑞医药=医疗' },
    { title: '第十批集采结果出炉，平均降价58%', expect: 'medical', reason: '集采=医疗' },
    { title: '药明康德营收124亿+28%，在手订单597亿', expect: 'medical', reason: '药明康德=医疗' },
    { title: '5G商用加速推进，三大运营商资本开支同比增长15%', expect: 'comm', reason: '5G/运营商=通信' },
    { title: '光模块需求持续旺盛，800G产品出货量同比增长280%', expect: 'comm', reason: '光模块=通信' },
    { title: '数据中心IDC行业景气度提升，机柜利用率回升至78%', expect: 'comm', reason: '数据中心=通信' },
    { title: '信创产业加速推进，国产通信芯片市占率提升至25%', expect: 'chip', reason: '信创优先匹配芯片' },
    { title: '央行开展3000亿元MLF操作，利率维持不变', expect: 'broad', reason: '央行/MLF=宽基' },
    { title: '北向资金今日净流入50亿元，加仓银行股', expect: 'broad', reason: '北向资金=宽基' },
    { title: '证监会发布衍生品交易监管新规', expect: 'broad', reason: '证监会/监管=宽基' },
    { title: '美联储维持利率不变，暗示年内可能降息', expect: 'broad', reason: '美联储=宽基' },
    { title: '特朗普宣布对华加征关税至60%', expect: 'broad', reason: '特朗普/关税=宽基' },
    { title: '4月CPI同比涨0.3%，PPI降幅收窄', expect: 'broad', reason: 'CPI/PPI=宽基' },
    { title: '国务院常务会议研究推进统一大市场建设', expect: 'broad', reason: '国务院=宽基' },
    { title: 'MSCI中国指数调整，新纳入22只A股', expect: 'broad', reason: 'MSCI/指数调整=宽基' },
    { title: '大唐环境附属拟5781.18万元出售大唐延安热电厂全部资产', expect: null, reason: '个股公告，非宏观非行业' },
    { title: '首程控股旗下基金投资中科沌序', expect: null, reason: '个股公告' },
    { title: '联想集团发布年度业绩 股东应占溢利19.12亿美元', expect: null, reason: '个股业绩' },
    { title: '瓶片加工费突破2000元/吨', expect: null, reason: '具体商品，非宏观' },
    { title: '日韩股市集体高开 韩股高开0.7%', expect: null, reason: '非美国国际+简单涨跌' },
    { title: '日本4月核心通胀降至四年低位', expect: null, reason: '日本，非美国' },
    { title: '日经指数或将上涨 受对美伊潜在协议提振', expect: null, reason: '日本股市' },
    { title: '美国德州就加密隐私问题起诉Meta和WhatsApp', expect: null, reason: '美国隐私诉讼，与中国互联网ETF无关' },
    { title: '股海导航_2026年5月22日_沪深股市公告与交易提示', expect: null, reason: '公告汇总，非行业新闻' },
    { title: '沪指收涨1.2% 两市成交额突破万亿', expect: null, reason: '市场涨跌，宽基排除' },
    { title: '创业板指收跌2.35% 半导体板块领跌', expect: null, reason: '指数涨跌+板块行情' },
    { title: 'A股收评：三大指数集体大跌', expect: null, reason: '收评类' },
    { title: '两融余额突破1.8万亿 创年内新高', expect: null, reason: '行业排除：两融余额' },
    { title: '特朗普再威胁伊朗交出浓缩铀，油价波动加剧', expect: 'broad', reason: '特朗普+油价=宽基国际政治' },
    { title: '摩根大通：全球动荡之际跨国企业转向中国避险', expect: 'broad', reason: '外资/避险=宽基' },
    { title: '4月社融增量1.2万亿 M2同比增长7.2%', expect: 'broad', reason: '社融/M2=宽基宏观' },
    { title: '发改委出台促消费新政，新能源车补贴延续', expect: 'broad', reason: '发改委/政策=宽基' },
    { title: '商务部回应中美贸易摩擦：坚决维护自身利益', expect: 'broad', reason: '商务部/中美=宽基' }
];

function categorizeNews(newsList) {
    var categories = { broad: [], internet: [], chip: [], medical: [], comm: [] };

    var keywords = {
        broad: ['A股', '上证', '沪深300', '创业板', '科创板', '央行', '逆回购', '外资', 'MSCI', '富时罗素', 'IPO', '退市', '监管', '证监会', '降息', '降准', '加息', 'LPR', 'MLF', '北向资金', '融资融券', '成交额', '财政部', '国务院', '发改委', '商务部', '关税', '特朗普', 'GDP', 'CPI', 'PPI', 'PMI', '通胀', '通缩', '利率', '人民币', '国债', '两融', '注册制', '美联储', '非农', '就业', '失业率', '制裁', '油价', '原油', '黄金', '避险', '美股', '纳斯达克', '标普', '美债', '美元', 'M1', 'M2', '社融', '信贷', '中美关系', '地缘政治', '俄乌', '中东', '指数调整', '纳入指数', '剔除指数', '杠杆资金', '融资余额', '沪港通', '深港通', '港股通', '立案调查', '行政处罚', '新规', '并购重组'],
        internet: ['腾讯', '阿里', '阿里巴巴', '腾讯控股', '京东', '京东集团', '美团', '快手', '拼多多', '百度', '网易', '哔哩哔哩', '小米', '小米集团', '字节跳动', '滴滴', '知乎', '微博', '阅文', '港股互联网', '互联网平台', '电商', '外卖', '本地生活', '在线教育', '社交', '游戏', '短视频', '直播', '云计算', '云服务', '港股通', '恒生科技', '科网', '中概股'],
        chip: ['半导体', '芯片', '集成电路', '晶圆', '光刻', '封装测试', '中芯国际', '韦尔股份', '卓胜微', '闻泰科技', '长电科技', '北方华创', '中微公司', '华虹半导体', '士兰微', '兆易创新', 'AI芯片', '算力芯片', '存储芯片', '先进封装', '半导体设备', '半导体材料', 'EDA', '国产替代', '信创'],
        medical: ['医药', '医疗', '创新药', '仿制药', '中药', '生物药', '化学药', '医疗器械', '医疗设备', '医疗耗材', '体外诊断', 'IVD', '药明康德', '迈瑞医疗', '恒瑞医药', '爱尔眼科', '智飞生物', '片仔癀', '爱美客', '华熙生物', '泰格医药', '康龙化成', '凯莱英', '集采', '医保谈判', '药品研发', '临床试验', 'CRO', 'CDMO', 'CXO', '医疗服务', '医药零售', '处方药'],
        comm: ['5G', '6G', '通信设备', '光通信', '光模块', '光纤', '数据中心', 'IDC', '云计算基础设施', '物联网', '物联网模组', '运营商', '信创', '国产替代', '紫光国微', '中兴通讯', '光环新网', '移远通信', '信维通信']
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

    var broadExclude = ['日本', '日经', '日元', '韩国', '韩股', '欧洲', '欧股', '德国', '法国', '英国', '澳洲', '印度', '越南', '新加坡', '泰国', '印尼', '巴西', '高开', '低开', '收盘涨跌', '股市收盘', '拟出售', '附属', '旗下基金', '发布公告', '年度业绩', '股东应占', '溢利', '加工费', '拟购', '拟收购', '拟转让', '作价', '万股', '亿元出售', '涨停', '跌停', '连板', '龙虎榜', '沪指收涨', '沪指收跌', '深证成指收涨', '深证成指收跌', '创业板指收涨', '创业板指收跌', '恒指收涨', '恒指收跌', '恒生科技收涨', '恒生科技收跌', '指数涨超', '指数跌超', '大盘涨', '大盘跌', '全线飘红', '全线飘绿', '集体大涨', '集体大跌', '市场概况', '市场一览', '市场速递', '行情速递', '最新股价', '今日股价', '实时行情', '股票行情', '股价查询', '股票代码', '茅台', '五粮液', '比亚迪', '宁德时代', '腾讯', '阿里', '美团', '中芯国际', '药明康德', '恒瑞医药', '迈瑞医疗', '爱尔眼科', '白酒板块', '半导体板块', '新能源车板块', '医药板块', '医疗板块', '锂电板块', 'A股收评', '港股收评', '美股收评', '午评', '两融余额', '融资余额', '融券余额', '黑色系早报', '工业品早报', '早报'];

    var used = {};
    var results = {};

    newsList.forEach(function(news) {
        var title = (news.title || '') + (news.intro || '') + (news.wap_intro || '');
        var newsKey = news.title || news.url || '';
        if (used[newsKey]) return;

        var isJunk = junkPatterns.some(function(p) { return title.includes(p); });
        if (isJunk) { results[newsKey] = { cat: null, reason: 'junk' }; return; }

        var isNonFinance = nonFinancePatterns.some(function(p) { return title.includes(p); });
        if (isNonFinance) { results[newsKey] = { cat: null, reason: 'nonFinance' }; return; }

        var matched = null;
        var excludedFromIndustry = false;

        for (var ci = 0; ci < industryCats.length; ci++) {
            var cat = industryCats[ci];
            if (keywords[cat].some(function(k) { return title.includes(k); })) {
                var isExcluded = industryExclude[cat] && industryExclude[cat].some(function(p) { return title.includes(p); });
                if (!isExcluded) {
                    matched = cat;
                    break;
                } else {
                    excludedFromIndustry = true;
                }
            }
        }

        if (!matched && keywords.broad.some(function(k) { return title.includes(k); })) {
            var isBroadExcluded = broadExclude.some(function(p) { return title.includes(p); });
            if (!isBroadExcluded) {
                matched = 'broad';
            }
        }

        if (!matched) {
            results[newsKey] = { cat: null, reason: excludedFromIndustry ? 'industryExcluded' : 'noMatch' };
            return;
        }

        if (categories[matched].length < limits[matched]) {
            categories[matched].push({ t: news.title || '暂无标题', i: '🟡', e: etfMap[matched], r: 0, b: news.intro || '', url: news.url || '#' });
            used[newsKey] = true;
            results[newsKey] = { cat: matched, reason: 'matched' };
        } else {
            results[newsKey] = { cat: matched, reason: 'limitFull' };
        }
    });

    return { categories: categories, results: results };
}

var passCount = 0;
var failCount = 0;
var failDetails = [];

testCases.forEach(function(tc) {
    var newsList = [{ title: tc.title, intro: '', url: tc.title }];
    var result = categorizeNews(newsList);
    var actual = result.results[tc.title] ? result.results[tc.title].cat : null;
    var passed = actual === tc.expect;

    if (passed) {
        passCount++;
    } else {
        failCount++;
        failDetails.push({ title: tc.title, expect: tc.expect, actual: actual, reason: tc.reason, detail: result.results[tc.title] });
    }
});

console.log('========================================');
console.log('  新闻分类测试结果');
console.log('========================================');
console.log('通过: ' + passCount + '/' + testCases.length);
console.log('失败: ' + failCount + '/' + testCases.length);
console.log('');

if (failDetails.length > 0) {
    console.log('❌ 失败用例详情:');
    failDetails.forEach(function(f, i) {
        console.log((i + 1) + '. 标题: ' + f.title);
        console.log('   期望: ' + (f.expect || '丢弃') + ' | 实际: ' + (f.actual || '丢弃') + ' | 原因: ' + f.reason);
        console.log('   详情: ' + JSON.stringify(f.detail));
        console.log('');
    });
} else {
    console.log('✅ 全部测试通过!');
}
