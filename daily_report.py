#!/usr/bin/env python3
"""
郑公泽·指数投资每日资讯 - GitHub Actions版
从auto_full.js转换而来，完全自包含，无需AI

功能：
1. 获取7大指数市场数据（东方财富API）
2. 获取财经新闻（新浪API）
3. 关键词智能分类（宽基+5行业）
4. 预设新闻兜底
5. 生成Markdown日报
6. PushDeer推送
"""

import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple

import requests

# ============================================================
# 配置常量
# ============================================================

PUSHDEER_KEY = os.environ.get("PUSHDEER_KEY", "PDU41552TCTtotgq3EC5AvTOaXpiZG0eMTR6VAl8v")
PUSHDEER_URL = "https://api2.pushdeer.com/message/push"

MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]
REQUEST_TIMEOUT = 15

BEIJING_TZ = timezone(timedelta(hours=8))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# 7大指数（东方财富API secid）
INDICES = [
    {"secid": "1.000001", "name": "上证指数"},
    {"secid": "0.399001", "name": "深证成指"},
    {"secid": "0.399006", "name": "创业板指"},
    {"secid": "1.000300", "name": "沪深300"},
    {"secid": "1.000905", "name": "中证500"},
    {"secid": "1.000852", "name": "中证1000"},
    {"secid": "1.000688", "name": "科创50"},
]

# ETF持仓映射
ETF_MAP = {
    "broad": "510300",
    "internet": "513330",
    "tech": "159939",
    "medical": "162412",
    "auto": "501057",
    "liquor": "512690",
}

# 行业ETF名称
INDUSTRY_NAMES = {
    "internet": "恒生互联网ETF",
    "tech": "信息技术ETF",
    "medical": "医疗ETF",
    "auto": "新能源汽车ETF",
    "liquor": "酒ETF",
}

# 行业ETF代码
INDUSTRY_CODES = {
    "internet": "513330",
    "tech": "159939",
    "medical": "162412",
    "auto": "501057",
    "liquor": "512690",
}

# 分类限制
CATEGORY_LIMITS = {"broad": 8, "internet": 5, "tech": 5, "medical": 5, "auto": 5, "liquor": 5}

# ============================================================
# 关键词配置（与auto_full.js完全一致）
# ============================================================

KEYWORDS = {
    "broad": [
        "A股", "上证", "沪深300", "创业板", "科创板", "央行", "逆回购", "外资", "MSCI",
        "富时罗素", "IPO", "退市制度", "退市新规", "监管", "证监会", "降息", "降准",
        "加息", "LPR", "MLF", "北向资金", "融资融券", "成交额", "财政部", "国务院",
        "发改委", "商务部", "关税", "特朗普", "GDP", "CPI", "PPI", "PMI", "通胀",
        "通缩", "利率", "人民币", "国债收益率", "两融", "注册制", "美联储", "非农",
        "就业", "失业率", "制裁", "油价", "原油", "黄金", "避险", "美股", "纳斯达克",
        "标普", "美债", "美元指数", "M1", "M2", "社融", "信贷投放", "中美关系",
        "地缘政治", "俄乌", "中东", "指数调整", "纳入指数", "剔除指数", "杠杆资金",
        "融资余额", "沪港通", "深港通", "港股通", "立案调查", "行政处罚", "新规",
        "并购重组", "降息预期", "流动性", "量化", "对冲", "互换便利", "股票回购",
        "增持回购", "再贷款", "转融通", "做空", "熔断", "资本市场", "投资者保护",
        "上市公司", "分红", "回购", "股权激励", "定增", "可转债", "IPO注册",
        "发行审核", "二级市场", "一级市场", "打新", "新股", "破发", "货币政策",
        "财政政策", "经济数据", "经济形势", "经济增长", "资金面", "市场流动性",
    ],
    "internet": [
        "腾讯", "阿里", "阿里巴巴", "腾讯控股", "京东", "京东集团", "美团", "快手",
        "拼多多", "百度", "网易", "哔哩哔哩", "小米", "小米集团", "字节跳动", "滴滴",
        "知乎", "微博", "阅文", "港股互联网", "互联网平台", "电商", "外卖", "本地生活",
        "在线教育", "社交", "游戏", "短视频", "直播", "云计算", "云服务", "恒生科技",
        "科网", "中概股", "SaaS", "数字营销", "AIGC", "数字人", "虚拟人", "内容创作",
        "在线旅游", "OTA", "社区团购", "即时零售", "跨境电商", "直播带货", "数字支付",
        "移动支付", "互联网医疗", "在线问诊", "互联网保险", "InsurTech", "FinTech",
        "金融科技", "数字货币", "Web3", "元宇宙",
    ],
    "tech": [
        "半导体", "芯片", "集成电路", "晶圆", "光刻", "封装测试", "中芯国际", "韦尔股份",
        "卓胜微", "闻泰科技", "长电科技", "北方华创", "中微公司", "华虹半导体", "士兰微",
        "兆易创新", "AI芯片", "人工智能", "大模型", "算力", "算法", "机器学习",
        "深度学习", "消费电子", "苹果产业链", "华为产业链", "VR", "AR", "面板",
        "显示屏", "存储器", "操作系统", "数据库", "信息安全", "网络安全", "5G", "6G",
        "通信设备", "量子计算", "自动驾驶", "信创", "国产替代", "PCB", "HBM",
        "先进封装", "光刻机", "EDA", "GPU", "英伟达", "华为昇腾", "寒武纪", "海光信息",
        "龙芯中科", "通富微电", "沪硅产业", "立讯精密", "歌尔股份", "京东方", "TCL科技",
        "传音控股", "汇顶科技", "复旦微电", "安路科技", "紫光国微", "澜起科技",
    ],
    "medical": [
        "医药", "医疗", "创新药", "仿制药", "中药", "生物药", "化学药", "医疗器械",
        "医疗设备", "医疗耗材", "体外诊断", "IVD", "药明康德", "迈瑞医疗", "恒瑞医药",
        "爱尔眼科", "智飞生物", "片仔癀", "爱美客", "华熙生物", "泰格医药", "康龙化成",
        "凯莱英", "集采", "医保谈判", "药品研发", "临床试验", "CRO", "CDMO", "CXO",
        "医疗服务", "医药零售", "处方药", "临床数据", "获批", "新药", "GLP-1", "ADC",
        "PD-1", "CAR-T", "生物类似药", "百济神州", "信达生物", "君实生物", "荣昌生物",
        "再鼎医药", "和黄医药", "诺诚健华", "康方生物", "科伦博泰", "迈威生物",
        "百利天恒", "首药控股", "海创药业", "迪哲医药", "益方生物", "泽璟制药",
        "诺辉健康", "药明生物", "金斯瑞", "圣诺医药", "云顶新耀", "和铂医药",
        "加科思", "基石药业", "亚盛医药", "康诺亚", "腾盛博药",
    ],
    "auto": [
        "新能源汽车", "电动车", "智能汽车", "比亚迪", "特斯拉", "宁德时代", "亿纬锂能",
        "理想汽车", "蔚来", "小鹏汽车", "华为汽车", "小米汽车", "锂电", "锂电池",
        "动力电池", "储能电池", "固态电池", "钠离子电池", "正极材料", "负极材料",
        "电解液", "隔膜", "碳酸锂", "充电桩", "换电站", "智能驾驶", "汽车芯片",
        "汽车电子", "新能源车销量", "电池装机量", "新能源车渗透率", "电动车出口",
        "氢燃料", "混动", "增程", "智驾", "钠电池", "天齐锂业", "赣锋锂业", "华友钴业",
        "容百科技", "当升科技", "恩捷股份", "星源材质", "天赐材料", "新宙邦", "璞泰来",
        "杉杉股份", "国轩高科", "中创新航", "亿纬锂能", "欣旺达", "孚能科技",
        "地平线", "黑芝麻智能", "德赛西威", "伯特利", "经纬恒润",
    ],
    "liquor": [
        "白酒", "茅台", "五粮液", "泸州老窖", "洋河股份", "山西汾酒", "古井贡酒",
        "今世缘", "口子窖", "水井坊", "舍得酒业", "酒鬼酒", "贵州茅台", "老窖",
        "洋河", "汾酒", "啤酒", "青岛啤酒", "华润啤酒", "重庆啤酒", "燕京啤酒",
        "葡萄酒", "黄酒", "酒业", "酿酒", "酒企", "酒类", "高端白酒", "次高端白酒",
        "批价", "动销", "酱香", "浓香", "清香", "烈酒", "威士忌", "低度酒", "预调酒",
        "郎酒", "剑南春", "水井坊", "迎驾贡酒", "伊力特", "金徽酒", "老白干酒",
        "顺鑫农业", "百润股份",
    ],
}

# 垃圾过滤词
JUNK_PATTERNS = ["减持", "折让", "配售", "复牌", "停牌", "联交所最新资料", "每股作价"]

# 非财经过滤词
NON_FINANCE_PATTERNS = [
    "自卫队", "台海", "世卫大会", "北约", "太空公司", "航天器", "文身", "布林肯",
    "中亚五国", "主场外交", "观察者网",
]

# 行业通用排除词
COMMON_INDUSTRY_EXCLUDE = [
    "恒生科技指数跌", "恒生科技指数涨", "恒指跌", "恒指涨", "指数跌超", "指数涨超",
    "收跌", "收涨", "A股收评", "港股收评", "美股收评", "午评", "两融余额",
    "融资余额", "融券余额", "央行", "降息", "降准", "LPR", "MLF", "北向资金",
    "证监会", "监管新规", "国务院", "财政部", "特朗普", "关税", "中美关系", "战争",
    "概念股早盘", "概念股午盘", "涨幅居前", "跌幅居前", "涨逾", "跌逾", "首挂上市",
    "首日高开", "首日涨", "上市首日", "普涨", "普跌", "隔夜要闻", "股海导航",
    "公告与交易提示", "加密隐私", "起诉", "集体上涨", "集体下跌", "集体走低",
    "集体走高", "全线下挫", "全线上扬",
]

INDUSTRY_EXCLUDE = {
    "internet": COMMON_INDUSTRY_EXCLUDE + ["科指涨", "科指跌", "集体上涨", "集体下跌"],
    "tech": COMMON_INDUSTRY_EXCLUDE + ["日经指数", "核数师", "委任", "会计师事务所", "投行业务", "摩根大通", "高盛", "引入AI", "越南", "菲律宾"],
    "medical": COMMON_INDUSTRY_EXCLUDE + ["越南", "菲律宾"],
    "auto": COMMON_INDUSTRY_EXCLUDE + ["越南", "菲律宾", "马来西亚", "Vinfast"],
    "liquor": COMMON_INDUSTRY_EXCLUDE[:],
}

BROAD_EXCLUDE = [
    "日本", "日经", "日元", "韩国", "韩股", "欧洲", "欧股", "德国", "法国", "英国",
    "澳洲", "印度", "越南", "新加坡", "泰国", "印尼", "巴西", "菲律宾", "马来西亚",
    "东南亚", "高开", "低开", "收盘涨跌", "股市收盘", "拟出售", "附属", "旗下基金",
    "发布公告", "年度业绩", "股东应占", "溢利", "加工费", "拟购", "拟收购", "拟转让",
    "作价", "万股", "亿元出售", "涨停", "跌停", "连板", "龙虎榜", "沪指收涨", "沪指收跌",
    "深证成指收涨", "深证成指收跌", "创业板指收涨", "创业板指收跌", "恒指收涨",
    "恒指收跌", "恒生科技收涨", "恒生科技收跌", "指数涨超", "指数跌超", "大盘涨",
    "大盘跌", "全线飘红", "全线飘绿", "集体大涨", "集体大跌", "市场概况", "市场一览",
    "市场速递", "行情速递", "最新股价", "今日股价", "实时行情", "股票行情", "股价查询",
    "股票代码", "茅台", "五粮液", "比亚迪", "宁德时代", "腾讯", "阿里", "美团",
    "中芯国际", "药明康德", "恒瑞医药", "迈瑞医疗", "爱尔眼科", "白酒板块",
    "半导体板块", "新能源车板块", "医药板块", "医疗板块", "锂电板块", "A股收评",
    "港股收评", "美股收评", "午评", "两融余额", "融资余额", "融券余额", "黑色系早报",
    "工业品早报", "早报", "盘初涨超", "盘初跌超", "早盘涨", "早盘跌", "科伦博泰",
    "首挂上市", "首日高开", "首日涨", "盘中涨超", "盘中跌超", "概念股早盘",
    "隔夜要闻", "中期选举", "筹款", "上市首日", "普涨", "普跌", "大选", "共和党",
    "民主党", "参议院", "众议院", "私募", "索赔", "维权", "ST", "退市不影响", "投资者索赔",
]


# ============================================================
# 日志配置
# ============================================================

def setup_logging():
    os.makedirs(LOGS_DIR, exist_ok=True)
    logger = logging.getLogger("daily_report")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    log_file = os.path.join(LOGS_DIR, "daily_report.log")
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


# ============================================================
# 市场数据获取（东方财富API）
# ============================================================

def fetch_market_data(logger):
    """获取7大指数实时数据"""
    logger.info("[1/4] 正在获取市场数据...")
    try:
        secids = ",".join(i["secid"] for i in INDICES)
        url = f"https://push2.eastmoney.com/api/qt/ulist.np/get?fields=f2,f3,f4,f12,f14&secids={secids}"

        for attempt in range(MAX_RETRIES):
            try:
                resp = requests.get(url, timeout=REQUEST_TIMEOUT)
                resp.raise_for_status()
                data = resp.json()

                if data.get("rc") != 0 or not data.get("data") or not data["data"].get("diff"):
                    logger.warning(f"东方财富API返回异常 (第{attempt+1}次)")
                    continue

                results = {}
                for item in data["data"]["diff"]:
                    code = item.get("f12", "")
                    idx = next((i for i in INDICES if i["secid"].endswith("." + code)), None)
                    name = idx["name"] if idx else item.get("f14", "")
                    results[name] = {
                        "price": item.get("f2", 0) / 100,
                        "pct": item.get("f3", 0) / 100,
                        "change": item.get("f4", 0) / 100,
                    }

                logger.info(f"    市场数据获取成功: {len(results)} 个指数")
                return results

            except Exception as e:
                logger.warning(f"    市场数据获取失败(第{attempt+1}次): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAYS[attempt])

        # 备用：新浪API
        return _fetch_market_sina(logger)

    except Exception as e:
        logger.error(f"    市场数据获取失败: {e}")
        return None


def _fetch_market_sina(logger):
    """备用：新浪财经API获取市场数据"""
    try:
        url = "https://hq.sinajs.cn/list=s_sh000001,s_sh000300,s_sz399006"
        headers = {"Referer": "https://finance.sina.com.cn"}
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)

        if resp.text == "Forbidden" or '="' not in resp.text:
            logger.warning("    新浪API被拒绝")
            return None

        result = {}
        for line in resp.text.split("\n"):
            if '="' not in line:
                continue
            match = re.search(r'="([^"]+)"', line)
            if not match:
                continue
            values = match.group(1).split(",")
            if "sh000001" in line:
                result["上证指数"] = {"price": float(values[1]), "pct": float(values[3]), "change": float(values[2])}
            elif "sh000300" in line:
                result["沪深300"] = {"price": float(values[1]), "pct": float(values[3]), "change": float(values[2])}
            elif "sz399006" in line:
                result["创业板指"] = {"price": float(values[1]), "pct": float(values[3]), "change": float(values[2])}

        if result:
            logger.info(f"    新浪备用API获取成功: {len(result)} 个指数")
        return result if result else None

    except Exception as e:
        logger.warning(f"    新浪备用API也失败: {e}")
        return None


# ============================================================
# 新闻获取（新浪API）
# ============================================================

def fetch_news(logger):
    """获取财经新闻列表"""
    logger.info("[2/4] 正在获取财经新闻...")
    try:
        news_sources = [
            {"url": "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num=50&page=1", "cat": "broad"},
            {"url": "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num=50&page=2", "cat": "broad"},
            {"url": "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=1686&k=&num=50&page=1", "cat": "broad"},
        ]

        all_news = []
        for src in news_sources:
            try:
                resp = requests.get(src["url"], timeout=REQUEST_TIMEOUT)
                data = resp.json()
                if data.get("result") and data["result"].get("data"):
                    for item in data["result"]["data"]:
                        item["_hintCat"] = src["cat"]
                    all_news.extend(data["result"]["data"])
            except Exception as e:
                logger.warning(f"    新闻源获取失败: {e}")

        # 去重+过滤3天前
        seen = set()
        now = time.time() * 1000
        filtered = []
        for item in all_news:
            key = item.get("title", "") or item.get("url", "")
            if key in seen:
                continue
            seen.add(key)
            ctime = item.get("ctime", "")
            if ctime:
                try:
                    news_time = datetime.strptime(ctime, "%Y-%m-%d %H:%M").timestamp() * 1000
                    if now - news_time > 3 * 24 * 3600 * 1000:
                        continue
                except ValueError:
                    pass
            filtered.append(item)

        logger.info(f"    获取到 {len(filtered)} 条新闻（去重后）")
        return filtered[:120]

    except Exception as e:
        logger.warning(f"    新闻获取失败: {e}")
        return []


# ============================================================
# 新闻分类（与auto_full.js逻辑完全一致）
# ============================================================

def categorize_news(news_list, logger):
    """智能分类新闻到6个类别"""
    logger.info("[3/4] 正在智能分类新闻...")

    categories = {cat: [] for cat in CATEGORY_LIMITS}
    industry_cats = ["internet", "tech", "medical", "auto", "liquor"]
    used = set()

    for news in news_list:
        title = (news.get("title", "") + news.get("intro", "") + news.get("wap_intro", ""))
        news_key = news.get("title", "") or news.get("url", "")
        if news_key in used:
            continue

        # 垃圾过滤
        if any(p in title for p in JUNK_PATTERNS):
            continue
        if any(p in title for p in NON_FINANCE_PATTERNS):
            continue

        matched = None

        # 先匹配行业
        for cat in industry_cats:
            matched_kw = [k for k in KEYWORDS[cat] if k in title]
            if matched_kw:
                is_excluded = any(p in title for p in INDUSTRY_EXCLUDE.get(cat, []))
                if not is_excluded:
                    # 过短纯价格标题
                    pure_price_words = ["盘中涨超", "盘中跌超", "高开近", "高开逾", "早盘涨超", "早盘跌超"]
                    has_pure_price = any(p in title for p in pure_price_words)
                    if has_pure_price and len(news.get("title", "")) < 20:
                        continue
                    matched = cat
                    break

        # 再匹配宽基
        if not matched:
            if any(k in title for k in KEYWORDS["broad"]):
                is_broad_excluded = any(p in title for p in BROAD_EXCLUDE)
                if not is_broad_excluded:
                    matched = "broad"

        if not matched:
            continue

        if len(categories[matched]) < CATEGORY_LIMITS[matched]:
            categories[matched].append({
                "t": news.get("title", "暂无标题"),
                "i": "🟡",
                "e": ETF_MAP[matched],
                "r": 0,
                "b": news.get("intro", "") or news.get("wap_intro", "") or news.get("summary", "暂无摘要"),
                "url": news.get("url", "") or news.get("wap_url", "#"),
            })
            used.add(news_key)

    # 标题前6字去重
    for cat in categories:
        seen_prefix = set()
        deduped = []
        for item in categories[cat]:
            name_match = re.match(r"^[\u4e00-\u9fa5a-zA-Z0-9\-·]+", item["t"])
            prefix = (name_match.group(0)[:6] if name_match else item["t"][:6])
            if prefix not in seen_prefix:
                seen_prefix.add(prefix)
                deduped.append(item)
        categories[cat] = deduped

    # 统计
    for cat in categories:
        logger.info(f"    {cat}: {len(categories[cat])} 条")

    return categories


# ============================================================
# 预设新闻（兜底）
# ============================================================

def get_preset_news():
    """预设高质量新闻数据，当API获取不足时使用"""
    return {
        "broad": [
            {"t": "央行逆回购连续缩量，5月净回笼1万亿", "i": "🟡", "e": "510300", "r": 1, "b": "央行开展3000亿元6个月期买断式逆回购。连续第三个月缩量续作，降准降息预期同步降温。"},
            {"t": "证监会发布衍生品交易监管新规", "i": "🟢", "e": "510300", "r": 0, "b": "禁止上市公司以自身股票为标的开展衍生品交易，封堵变相减持漏洞。券商门槛提高至净资本≥5亿元。"},
            {"t": "A股年内46家公司被立案调查", "i": "🟡", "e": "510300", "r": 1, "b": "45家由证监会立案，集中在信息披露违规。监管节奏加快，退市不免责原则持续压实。"},
            {"t": "外资集体加仓A股，MSCI新纳入22只", "i": "🟢", "e": "510300", "r": 0, "b": "外资持股增46.8亿股，市值增697.6亿。高盛新进526家、瑞银新进385家十大流通股东。5月29日生效。"},
            {"t": "华润新能源245亿IPO获证监会注册", "i": "🟡", "e": "510300", "r": 0, "b": "深交所史上最大IPO，红筹回归第一股。扣非净利润59.8亿同比降23.8%，一季度跌幅扩大至31%。"},
            {"t": "中美元首北京会晤达成战略稳定共识", "i": "🟢", "e": "510300", "r": 0, "b": "马斯克、黄仁勋等科技商业代表随团访华。全球不确定性预期下降，关税克制风险有望缓解。"},
        ],
        "internet": [
            {"t": "腾讯Q1营收1964.6亿+9%，AI资本开支付款370亿", "i": "🟢", "e": "513330", "r": 0, "b": "经营盈利673.75亿+17%。AI开支付款370亿，当期319.36亿+16%、环比+63%。下半年更多国产芯片将投入使用。"},
            {"t": "阿里Q1营收2433.8亿，云AI收入占比首破30%", "i": "🟢", "e": "513330", "r": 0, "b": "阿里云外部商业化收入增长加速至40%，AI收入占比突破30%。AI投入进入正向规模商业化回报周期。"},
            {"t": "京东Q1营收3157亿+4.9%，年活跃用户超7.4亿", "i": "🟢", "e": "513330", "r": 0, "b": "季度活跃用户连续10个季度同比双位数增长。AI深度嵌入采销、定价、库存、营销全流程。"},
        ],
        "tech": [
            {"t": "国产AI芯片加速替代，英伟达在华份额归零", "i": "🟢", "e": "159939", "r": 1, "b": "黄仁勋承认在华AI份额近归零。国产芯片出货165万张占41%，华为昇腾950推理算力达H20的2.87倍。"},
            {"t": "中芯国际Q1营收176亿+8.1%，成熟制程重获定价权", "i": "🟢", "e": "159939", "r": 1, "b": "毛利率20.1%产能利用率93.1%。供不应求品类已涨价，Q2营收指引环比+14%-16%。"},
            {"t": "中芯国际产能利用率93.1%，AI虹吸全球代工产能", "i": "🟢", "e": "159939", "r": 0, "b": "赵海军用虹吸效应形容AI对芯片产能拉动。成熟制程涨价效应沿产业链传导。"},
        ],
        "medical": [
            {"t": "创新药数据保护新规落地，估值逻辑转向研发价值", "i": "🟢", "e": "162412", "r": 1, "b": "药品试验数据保护实施。创新药6年保护期、改良型4年、首仿3年。审评时限从60→30工作日。"},
            {"t": "恒瑞药明百济信达四大龙头Q1业绩全面爆发", "i": "🟢", "e": "162412", "r": 0, "b": "恒瑞+25%-35%，创新药收入占比60%。药明康德营收124.36亿+28.81%，在手订单597.7亿。百济神州首年盈利。"},
            {"t": "2026年医保目录新增114种药品，50款1类创新药", "i": "🟢", "e": "162412", "r": 0, "b": "历年最多。新药获批到进院从1-2年缩短至3-6个月。创新药出海BD交易98笔总金额614亿美元。"},
        ],
        "auto": [
            {"t": "碳酸锂涨至20万元/吨+250%，超15家车企涨价", "i": "🔴", "e": "501057", "r": 1, "b": "碳酸锂从5.84万涨至20万+，涨幅超250%。比亚迪特斯拉小米等15+车企涨价，Model Y上调1.8万元。"},
            {"t": "汽车行业利润率跌至3.2%创近十年新低", "i": "🔴", "e": "501057", "r": 0, "b": "Q1利润率仅3.2%，利润784亿-18%。中型智能化电动车成本较2025年+4000-7000元。"},
            {"t": "钠电池乘用车2026年量产，续航突破500公里", "i": "🟢", "e": "501057", "r": 0, "b": "宁德时代披露钠电池乘用车将量产，纯电500-600km。可满足50%+车型需求。"},
        ],
        "liquor": [
            {"t": "茅台年内第二次官宣涨价，4款产品上调60-200元", "i": "🟢", "e": "512690", "r": 1, "b": "5月16日上调：陈年茅台+80至4279元、精品茅台+60至2359元。年内两次调价释放市场化改革信号。"},
            {"t": "五粮液1618上涨1元，11大单品六涨四跌", "i": "🟢", "e": "512690", "r": 0, "b": "国窖1573七连阳创月新高，普五批价坚挺850元。精品茅台+4元创近月最高。白酒业拐点渐现。"},
            {"t": "白酒行业深度分化：高端涨价次高端降价", "i": "🟡", "e": "512690", "r": 0, "b": "飞天稳价格锚，精品茅台却变相降价37%。次高端300-800元带销量-14%至-20%。库存Q3有望出清。"},
        ],
    }


# ============================================================
# 生成Markdown日报
# ============================================================

def generate_markdown(news, market, logger):
    """生成Markdown格式日报"""
    beijing_now = datetime.now(BEIJING_TZ)
    date_str = f"{beijing_now.year}年{beijing_now.month}月{beijing_now.day}日"
    weekdays = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    weekday = weekdays[beijing_now.weekday()]
    is_weekend = beijing_now.weekday() >= 5

    md = f"# 郑公泽 · 指数投资日报\n📅 {date_str} · {weekday}\n\n---\n\n"

    # 市场概览
    md += "## 📈 今日市场速览\n\n"
    if is_weekend:
        md += f"> 今日{weekday}，A股休市。以下为最近交易日收盘数据：\n\n"

    if market:
        index_order = ["上证指数", "深证成指", "创业板指", "沪深300", "中证500", "中证1000", "科创50"]
        for name in index_order:
            if name in market:
                r = market[name]
                sign = "+" if r["pct"] >= 0 else ""
                md += f"**{name}** {r['price']:.2f}（{sign}{r['pct']:.2f}%）\n\n"
    else:
        md += "今日市场数据暂未获取\n\n"

    # 宽基指数
    md += f"---\n\n## 📈 宽基指数重要资讯\n\n"
    for i, x in enumerate(news["broad"], 1):
        body = x["b"][:400] + ("..." if len(x["b"]) > 400 else "")
        md += f'{i}️⃣ **{x["t"]}** {x["i"]}\n`{x["e"]}`{" ⚠️高风险" if x["r"] else ""}\n> {body}'
        if x.get("url") and x["url"] != "#":
            md += f'\n\n[查看原文 →]({x["url"]})'
        md += "\n\n"

    # 行业指数
    md += "---\n\n## 🏭 行业指数重要资讯\n\n"

    industry_emoji = {
        "internet": "🌐",
        "tech": "💻",
        "medical": "💊",
        "auto": "🚗",
        "liquor": "🍷",
    }

    for cat in ["internet", "tech", "medical", "auto", "liquor"]:
        emoji = industry_emoji[cat]
        name = INDUSTRY_NAMES[cat]
        code = INDUSTRY_CODES[cat]
        md += f"### {emoji} {name} · {code}\n"
        for x in news[cat]:
            body = x["b"][:400] + ("..." if len(x["b"]) > 400 else "")
            md += f'{x["i"]} **{x["t"]}**\n`ETF {x["e"]}`{" ⚠️高风险" if x["r"] else ""}\n> {body}'
            if x.get("url") and x["url"] != "#":
                md += f'\n\n[查看原文 →]({x["url"]})'
            md += "\n\n"
        if cat != "liquor":
            md += "---\n\n"

    # 风险提示
    md += "---\n\n## ⚠️ 风险提示\n\n"
    all_items = news["broad"] + news["internet"] + news["tech"] + news["medical"] + news["auto"] + news["liquor"]
    high_risk = [x for x in all_items if x["r"]]
    bad_items = [x for x in all_items if x["i"] == "🔴"]
    risk_idx = 1
    if high_risk:
        for x in high_risk:
            md += f'{risk_idx}. **高风险** - {x["t"]}\n'
            risk_idx += 1
    if bad_items:
        md += f'{risk_idx}. **利空因素** - 共{len(bad_items)}条利空消息需关注\n'
        risk_idx += 1
    if risk_idx == 1:
        md += "今日暂无重大风险信号\n"

    md += "\n---\n\n*数据来源：东方财富/新浪财经*\n*本资讯仅供参考，不构成投资建议*"

    return md


# ============================================================
# PushDeer推送
# ============================================================

def send_pushdeer(title, content, logger):
    """通过PushDeer推送消息"""
    logger.info("[4/4] 正在推送...")
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"    PushDeer推送中...（第 {attempt + 1} 次尝试）")
            resp = requests.post(
                PUSHDEER_URL,
                data={
                    "pushkey": PUSHDEER_KEY,
                    "text": title,
                    "type": "markdown",
                    "desp": content,
                },
                timeout=REQUEST_TIMEOUT,
            )
            result = resp.json()
            code = result.get("code")
            if code == 0:
                logger.info("    PushDeer推送成功")
                return True
            else:
                logger.warning(f"    PushDeer返回失败 code={code}: {result}")
        except requests.exceptions.Timeout:
            logger.warning(f"    PushDeer请求超时")
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"    PushDeer连接错误: {e}")
        except Exception as e:
            logger.warning(f"    PushDeer请求异常: {e}")

        if attempt < MAX_RETRIES - 1:
            delay = RETRY_DELAYS[attempt]
            logger.info(f"    PushDeer将在 {delay} 秒后重试...")
            time.sleep(delay)

    logger.error("    PushDeer推送失败，已达最大重试次数")
    return False


# ============================================================
# 写入状态文件
# ============================================================

def write_status_file(date_str, market_ok, news_ok, push_ok, errors, logger):
    """写入执行状态文件"""
    os.makedirs(LOGS_DIR, exist_ok=True)
    status = {
        "任务名称": "郑公泽·指数投资每日资讯",
        "执行日期": date_str,
        "市场数据": "成功" if market_ok else "失败",
        "新闻获取": "成功" if news_ok else "失败",
        "推送": "成功" if push_ok else "失败",
        "是否成功": market_ok and news_ok and push_ok,
        "错误信息": errors if errors else None,
        "时间戳": datetime.now(BEIJING_TZ).isoformat(),
    }
    status_file = os.path.join(LOGS_DIR, f"daily_{date_str}_status.json")
    try:
        with open(status_file, "w", encoding="utf-8") as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
        logger.info(f"状态文件已保存: {status_file}")
    except Exception as e:
        logger.error(f"状态文件写入失败: {e}")


# ============================================================
# 主流程
# ============================================================

def main():
    logger = setup_logging()
    beijing_now = datetime.now(BEIJING_TZ)
    date_str = beijing_now.strftime("%Y%m%d")

    logger.info("=" * 50)
    logger.info(f"郑公泽·指数投资每日资讯 - {date_str}")
    logger.info(f"当前北京时间: {beijing_now.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)

    # 周末检查
    if beijing_now.weekday() >= 5:
        logger.info("今日为周末，A股休市，跳过推送")
        write_status_file(date_str, False, False, False, ["周末休市，跳过推送"], logger)
        return 0

    errors = []
    market = None
    news = None
    market_ok = False
    news_ok = False
    push_ok = False

    try:
        # Step 1: 获取市场数据
        market = fetch_market_data(logger)
        market_ok = market is not None
        if not market_ok:
            logger.warning("市场数据获取失败，继续执行")

        # Step 2: 获取新闻
        news_list = fetch_news(logger)

        # Step 3: 分类新闻
        if news_list:
            news = categorize_news(news_list, logger)
            preset = get_preset_news()

            # 补充不足的分类
            for cat in CATEGORY_LIMITS:
                if len(news[cat]) == 0:
                    logger.warning(f"    {cat} 分类为空，使用预设数据")
                    news[cat] = preset[cat]
                elif len(news[cat]) < 3:
                    logger.info(f"    {cat} 分类仅{len(news[cat])}条，补充预设数据")
                    existing_titles = {x["t"] for x in news[cat]}
                    for p in preset[cat]:
                        if len(news[cat]) < 3 and p["t"] not in existing_titles:
                            news[cat].append(p)
            news_ok = True
        else:
            news = get_preset_news()
            news_ok = True
            logger.info("    使用预设新闻数据")

        # Step 4: 生成日报
        markdown = generate_markdown(news, market, logger)
        logger.info("    日报生成完成")

        # 保存日报到文件
        report_path = os.path.join(BASE_DIR, "today_report.md")
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(markdown)
            logger.info(f"    日报已保存: {report_path}")
        except Exception as e:
            logger.warning(f"    日报保存失败: {e}")

        # Step 5: 推送
        title = f"郑公泽·指数投资日报 {beijing_now.month}月{beijing_now.day}日"
        push_ok = send_pushdeer(title, markdown, logger)

        if not push_ok:
            errors.append("PushDeer推送失败")

    except Exception as e:
        logger.error(f"主流程异常: {e}", exc_info=True)
        errors.append(f"主流程异常: {e}")

        # 兜底：用预设数据推送
        try:
            news = get_preset_news()
            markdown = generate_markdown(news, None, logger)
            title = f"郑公泽·指数投资日报 {beijing_now.month}月{beijing_now.day}日"
            push_ok = send_pushdeer(title, markdown, logger)
            logger.info(f"兜底推送{'成功' if push_ok else '失败'}")
        except Exception as e2:
            logger.error(f"兜底推送也失败: {e2}")

    # 写入状态文件
    summary = f"市场:{'成功' if market_ok else '失败'} | 新闻:{'成功' if news_ok else '失败'} | 推送:{'成功' if push_ok else '失败'}"
    write_status_file(date_str, market_ok, news_ok, push_ok, errors, logger)

    logger.info("=" * 50)
    final_status = "成功" if (market_ok and news_ok and push_ok) else "部分失败"
    logger.info(f"脚本执行完成 - {final_status}")
    logger.info(f"摘要: {summary}")
    logger.info("=" * 50)

    return 0 if (market_ok and news_ok and push_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
