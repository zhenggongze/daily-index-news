
const dataPatterns = [
    /\d+\.?\d*%/, /\d+\.?\d*亿/, /\d+\.?\d*万/, /\d+\.?\d*元/,
    /\d+\.?\d*美元/, /\d+\.?\d*点/, /\d+\.?\d*倍/, /同比[+-]?\d/,
    /环比[+-]?\d/, /增长\d/, /下降\d/, /提升\d/, /减少\d/,
    /突破\d/, /跌破\d/, /升至\d/, /降至\d/, /超过\d/, /高达\d/
];

// 测试第一个新闻摘要
const summary = '2026年4月美国CPI同比涨3.8%、PPI同比涨6.0%，创下2022年12月以来新高。野村证券直接撤回年内降息预测，高盛把首次降息推迟到年末，市场定价全年不降息概率超80%。对全球流动性环境产生边际收紧影响，外资流入节奏可能放缓。';

console.log('测试摘要:', summary);
console.log('-------------------');
console.log('开始检查每个模式:');

let dataCount = 0;
for (const pat of dataPatterns) {
    if (pat.test(summary)) {
        console.log('匹配到:', pat);
        dataCount++;
    }
}

console.log('-------------------');
console.log('总计数据点:', dataCount);
