#!/usr/bin/env python3
"""
GitHub Actions 每日资讯全自动流水线
1. 获取7大指数行情（东方财富API）
2. 拉取新浪财经200条头条
3. 读取ETF持仓和历史记录
4. 调用DeepSeek按prompt_update_v2.txt规则生成报告
5. 质量自检 → 不通过则重试（最多3次）
6. PushDeer推送
"""
import os, sys, json, re, time, requests
from datetime import datetime, date, timedelta

# ========== 配置 ==========
DEEPSEEK_KEY = "sk-350f6fd5bb314a72b62538cfa31f854e"
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-v4-flash"
PUSHDEER_KEY = os.environ.get("PUSHDEER_KEY", "PDU41552TCTtotgq3EC5AvTOaXpiZG0eMTR6VAl8v")
PUSHDEER_URL = "https://api2.pushdeer.com/message/push"
PUSH_TITLE = "Trae每日指数投资资讯"

# ========== 获取市场数据 ==========
def fetch_market_data():
    """通过东方财富API获取7大指数"""
    secids = "1.000001,0.399001,0.399006,1.000300,1.000905,1.000852,1.000688"
    url = f"https://push2.eastmoney.com/api/qt/ulist.np/get?fields=f2,f3,f4,f12,f14&secids={secids}"
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
        if data.get("rc") != 0 or not data.get("data", {}).get("diff"):
            print("MARKET_FETCH_FAILED: API returned error")
            return None

        name_map = {"000001": "上证指数", "399001": "深证成指", "399006": "创业板指",
                     "000300": "沪深300", "000905": "中证500", "000852": "中证1000", "000688": "科创50"}
        results = {}
        for item in data["data"]["diff"]:
            code = item["f12"]
            nm = name_map.get(code, item.get("f14", code))
            price = item["f2"] / 100
            pct = item["f3"] / 100
            results[nm] = {"price": price, "pct": pct}

        order = ["上证指数", "深证成指", "创业板指", "沪深300", "中证500", "中证1000", "科创50"]
        lines = []
        for nm in order:
            if nm in results:
                r = results[nm]
                sign = "+" if r["pct"] >= 0 else ""
                lines.append(f"**{nm}** {r['price']:.2f}（{sign}{r['pct']:.2f}%）")

        today = date.today()
        wd = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        return {
            "date": f"{today.year}年{today.month}月{today.day}日",
            "weekday": wd[today.weekday()],
            "is_weekend": today.weekday() >= 5,
            "indices": results,
            "markdown": "\n".join(lines)
        }
    except Exception as e:
        print(f"MARKET_FETCH_ERROR: {e}")
        return None

# ========== 获取新闻 ==========
def fetch_news():
    """从新浪财经API拉取200条最近新闻"""
    all_news = []
    seen = set()

    for page in [1, 2, 3, 4]:
        url = f"https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num=50&page={page}"
        try:
            r = requests.get(url, timeout=15, headers={"Referer": "https://finance.sina.com.cn"})
            data = r.json()
            if data.get("result", {}).get("data"):
                for item in data["result"]["data"]:
                    title = (item.get("title") or "").strip()
                    intro = (item.get("intro") or item.get("summary") or "").strip()
                    key = title
                    if key and key not in seen and len(title) > 5 and len(title) < 100:
                        seen.add(key)
                        ctime = item.get("ctime", "")
                        all_news.append({"title": title, "intro": intro, "ctime": ctime})
        except Exception as e:
            print(f"NEWS_PAGE_{page}_ERROR: {e}")

    print(f"获取到 {len(all_news)} 条新闻")
    return all_news

# ========== 读取本地文件 ==========
def read_system_prompt():
    try:
        with open("prompt_update_v2.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

def read_etf_holdings():
    try:
        with open("etf_holdings.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"holdings": {}}

def read_history():
    try:
        with open("news_history.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

# ========== 调用DeepSeek生成报告 ==========
def generate_report(market_data, news_list, system_prompt, etf_holdings, history):
    """将全量数据发给DeepSeek，按system_prompt规则生成日报"""

    # 构建新闻上下文
    news_context = "\n".join([
        f"[{i+1}] {n['title']}\n    {n.get('intro','')[:200]}"
        for i, n in enumerate(news_list)
    ])

    # 构建历史去重上下文
    today_key = date.today().isoformat()
    history_items = []
    for d in range(1, 4):
        past = (date.today() - timedelta(days=d)).isoformat()
        if past in history:
            history_items.extend(history[past])
    history_context = "\n".join([f"  - {t}" for t in history_items]) if history_items else "(空)"

    # ETF持仓
    holdings_context = json.dumps(etf_holdings.get("holdings", {}), ensure_ascii=False, indent=2)

    user_msg = f"""请严格按照系统规则生成今日的指数投资日报。

## 今日日期：{market_data['date']} {market_data['weekday']}

## 7大指数行情（仅作背景参考，无需输出为单独小节：）
{market_data['markdown']}

## ETF前5大持仓（从etf_holdings.json读取）
{holdings_context}

## 近3天历史新闻标题（避免重复）
{history_context}

## 今日200条新闻标题+摘要（从新浪财经实时抓取，从中筛选）
{news_context}

## 硬约束：
1. 宽基8条 + 4行业x5条 = 28条，只多不少
2. 每条标题：**N️⃣ 标题 🟢/🔴/⚪**
3. 每条摘要：> 80字以上，含≥2个量化数据点（%|亿|万|元|美元|点|倍|bp|基点|个百分点），含≥1个投资逻辑判断，禁用**加粗，不禁用icon开头
4. 宽基禁止：个股/逆回购/MLF/场外期权/净资本/国债期货/LPR/SLF/PSL/XX板块等
5. 行业个股只允许前5大持仓或重点关注公司
6. 芯片ETF与通信ETF以光模块为边界
7. 标题第1行必须是📅日期行，推送标题会自动替换
8. **禁止输出"## 📈 今日市场速览"小节**
9. **禁止在新闻中出现"行业级别""前5大持仓个股""### 行业级别""### 前5大持仓个股"等分节标记**
10. **ETF标题只允许"## 🌐 ETF名称(代码)"格式，禁止加副标题**
11. **所有新闻直接以**N️⃣标题 标签**格式连续排列，不插入###小标题**"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg}
    ]

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 8192
    }

    try:
        r = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=120)
        data = r.json()
        if "choices" in data:
            content = data["choices"][0]["message"]["content"]
            # 写入本地供调试
            with open("today_report.md", "w", encoding="utf-8") as f:
                f.write(content)
            return content
        else:
            print(f"LLM_ERROR: {json.dumps(data, ensure_ascii=False)[:500]}")
            return None
    except Exception as e:
        print(f"LLM_REQUEST_ERROR: {e}")
        return None

# ========== 质量自检 ==========
def validate_report(report_path="today_report.md"):
    """简版校验，不依赖Node.js"""
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
    except:
        return False, ["文件不存在"]

    errors = []
    # 基本检查
    if len(content) < 5000:
        errors.append(f"内容过短: {len(content)}字")
    if "芯片ETF(159995)" not in content:
        errors.append("缺少芯片ETF小节")
    if "通信ETF(515880)" not in content:
        errors.append("缺少通信ETF小节")
    if "恒生互联网ETF" not in content:
        errors.append("缺少恒生互联网ETF小节")
    if "医疗ETF" not in content:
        errors.append("缺少医疗ETF小节")

    # 新闻条数
    news_count = len(re.findall(r'\*\*\d️⃣', content))
    if news_count < 28:
        errors.append(f"新闻不足28条: 仅{news_count}条")

    # 数据点检查
    data_pattern = re.compile(r'\d+\.?\d*(?:%|亿|万|元|美元|点|倍|bp|基点|个百分点)')
    items = re.findall(r'\*\*\d️⃣\s*(.+?)\*\*\s*(🔴|🟢|⚪)', content)
    data_point_errors = 0
    for title, tag in items:
        idx = content.find(title)
        summary_start = content.find(">", idx) if idx >= 0 else -1
        if summary_start >= 0:
            summary_end = content.find("\n\n", summary_start)
            if summary_end < 0:
                summary_end = min(len(content), summary_start + 1000)
            summary = content[summary_start:summary_end]
            if len(data_pattern.findall(summary)) < 2:
                data_point_errors += 1
    if data_point_errors > 3:
        errors.append(f"数据点不足的摘要超过3条: {data_point_errors}条")

    pass_check = len(errors) == 0
    if errors:
        print(f"VALIDATION_FAILED: {'; '.join(errors)}")
    else:
        print(f"VALIDATION_PASSED: {news_count}条新闻")
    return pass_check, errors

# ========== 推送 ==========
def push_report():

    try:
        with open("today_report.md", "r", encoding="utf-8") as f:
            content = f.read()
    except:
        print("PUSH_SKIP: no report file")
        return False

    if len(content) < 5000:
        print(f"PUSH_SKIP: too short ({len(content)} chars)")
        return False

    for attempt in range(1, 4):
        try:
            r = requests.post(PUSHDEER_URL,
                data={"pushkey": PUSHDEER_KEY, "text": PUSH_TITLE, "type": "markdown", "desp": content},
                timeout=30)
            j = r.json()
            if j.get("code") == 0:
                print("PUSH_SUCCESS")
                return True
            else:
                print(f"PUSH_FAILED:{j.get('error','unknown')}")
        except Exception as e:
            print(f"REQUEST_ERROR:{e}")
        if attempt < 3:
            time.sleep(3)

    print("PUSH_FAILED:max_retries_exceeded")
    return False

# ========== 主流程 ==========
def main():
    today = date.today()
    if today.weekday() >= 5:
        print(f"WEEKEND: {today.weekday()}, skipping")
        return

    print("=" * 40)
    print(f"[{today.isoformat()}] 开始每日资讯流水线")
    print("=" * 40)

    # 1. 市场数据（非致命，失败则使用占位）
    print("\n[1/5] 获取市场数据...")
    market = fetch_market_data()
    if not market:
        print("MARKET_FETCH_FAILED: 行情暂不可用，继续生成（无行情数据）")
        today = date.today()
        wd = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        market = {
            "date": f"{today.year}年{today.month}月{today.day}日",
            "weekday": wd[today.weekday()],
            "is_weekend": today.weekday() >= 5,
            "indices": {},
            "markdown": "（行情数据暂不可用）"
        }
    print(f"  日期: {market['date']} {market['weekday']}")

    # 2. 新闻
    print("\n[2/5] 拉取新闻...")
    news = fetch_news()
    if len(news) < 50:
        print(f"NEWS_TOO_FEW: only {len(news)}, continuing anyway")

    # 3. 本地资源
    print("\n[3/5] 读取规则和持仓...")
    system_prompt = read_system_prompt()
    etf_holdings = read_etf_holdings()
    history = read_history()

    # 4. 生成报告
    for attempt in range(1, 4):
        print(f"\n[4/5] 第{attempt}次尝试生成报告...")
        report = generate_report(market, news, system_prompt, etf_holdings, history)
        if not report:
            print("  LLM生成失败")
            continue

        print(f"  报告长度: {len(report)} 字")
        passed, errors = validate_report()
        if passed:
            break
        print(f"  => 重试 (剩余{3-attempt}次)")
    else:
        print("MAX_RETRIES_EXCEEDED: 3次生成均未通过校验")

    # 5. 推送
    print("\n[5/5] 推送...")
    push_report()

if __name__ == "__main__":
    main()
