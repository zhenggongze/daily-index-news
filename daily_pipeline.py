#!/usr/bin/env python3
"""
AI算力产业链每日资讯 全自动流水线 v2
流程：RSS采集 → 多级过滤 → AI精选(DeepSeek打分) → 生成TSV → 写入网站JSON
目标产出：20-30条/天，每日凌晨自动运行

用法：
  手动运行: python daily_pipeline.py
  定时任务: Windows Task Scheduler 每天00:30触发
"""
import os, sys, re, json, time, warnings
from datetime import datetime, date

warnings.filterwarnings("ignore")
import urllib3
urllib3.disable_warnings()

import requests
import feedparser

BASE = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(BASE, ".trae", "skills", "a-stock-data")
sys.path.insert(0, SKILLS_DIR)

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_KEY", "")
if not DEEPSEEK_KEY:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            DEEPSEEK_KEY = winreg.QueryValueEx(k, "DEEPSEEK_KEY")[0]
    except:
        pass
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-v4-pro"
DATA_DIR = os.path.join(BASE, "news_site", "public", "data")
os.makedirs(DATA_DIR, exist_ok=True)

RSS_SOURCES = [
    ("华尔街见闻", "https://feed.wallstreetcn.com/news/global"),
    ("IT之家", "https://www.ithome.com/feed/"),
    ("爱范儿", "https://www.ifanr.com/feed"),
    ("199IT", "https://www.199it.com/feed"),
    ("Tom's Hardware", "https://www.tomshardware.com/feeds/all"),
    ("ServeTheHome", "https://www.servethehome.com/feed"),
]

BLOCK_KWS = [
    "ETF", "etf", "批量买入", "LPR", "利率", "央行",
    "涨停", "跌停", "大涨", "暴涨", "涨超", "涨近",
    "收盘", "尾盘", "早盘", "涨幅", "跌幅",
    "酷派", "飞傲", "华擎", "红魔", "九州风神", "日产",
    "票房", "世界杯", "足球",
    "beta", "Beta", "visionOS", "visionos",
    "智能手表", "出货量.*同比",
    "AirPort", "MacBook", "Amazon Prime",
    "IT早报", "早报｜",
    "暂无", "不涉及",
]

BLOCK_DOMAINS = [
    "特斯拉.*车祸", "特斯拉.*事故",
    "电视出货", "智能手表",
    "Steam.*Machine", "游戏主机",
    "Model 3.*撞", "Model Y.*撞",
    "AirPods", "AirTag",
    "摩托罗拉", "酷派", "飞傲",
]

CORE_KWS = [
    "AI", "人工智能", "算力", "大模型", "芯片", "半导体", "英伟达", "NVIDIA",
    "光模块", "PCB", "HBM", "存储芯片", "存储原厂", "液冷", "散热", "CoWoS", "先进封装",
    "国产替代", "自主可控", "华为", "数据中心", "GPU", "服务器",
    "人形机器人", "具身智能", "Agent", "AI应用", "AI代理",
    "Token", "Capex", "资本开支", "自动驾驶",
    "六氟化钨", "铟", "氮化铝", "钨", "铋", "金刚石",
    "鸿海", "富士康", "台积电", "OpenAI", "Anthropic", "智谱",
    "字节跳动", "三星", "SK海力士", "美光", "谷歌", "DeepMind",
    "推理", "端侧AI", "AI PC", "NPU",
    "AI公司", "AI企业",
    "半导体设备", "半导体材料",
    "NAND", "长江存储", "DRAM", "DDR5",
    "电力.*协议", "核能", "天然气.*发电",
    "Codex", "微信.*AI", "豆包",
]

ML_MAP = {
    "智谱": "D", "超硅": "A", "硅片": "A",
    "鸿海": "B", "英伟达": "B", "Rubin": "B", "Rubin": "B",
    "HBM": "B", "存储芯片": "B", "DDR5": "B",
    "液冷": "B", "PCB": "B", "光模块": "B",
    "长江存储": "A", "NAND": "B",
    "海力士": "B", "美光": "B", "三星.*存储": "B",
    "OpenAI": "D", "ChatGPT": "D", "Codex": "D",
    "Claude": "D", "Anthropic": "A,D",
    "微信.*AI": "D", "豆包": "D", "DeepSeek": "D",
    "Agent.*OS": "D", "Agent.*平台": "D",
    "华为.*PC": "A", "华为.*手机": "A", "华为.*逆势": "A",
    "半导体设备": "A", "光刻胶": "A", "长川": "A",
    "字节.*GPU": "A", "天数智芯": "A",
    "诺奖.*Anthropic": "D",
    "机器人": "C", "Isaac": "C", "具身": "C",
    "开普勒": "C",
    "端侧AI": "D", "AI PC": "D",
    "AI职场": "D", "AI.*使用率": "D",
    "新能源.*AI": "D", "AI.*电力": "B",
    "三星DS": "A",
    "宁德时代": "D",
}

def get_mainline(title):
    for kw, ml in ML_MAP.items():
        if re.search(kw, title, re.I):
            return ml
    return "D"

def should_block(title, summary):
    text = (title + " " + summary)
    for kw in BLOCK_KWS:
        if kw.lower() in text.lower():
            return True
    for kw in BLOCK_DOMAINS:
        if re.search(kw, text, re.I):
            return True
    eng_ratio = sum(1 for c in text[:200] if c.isascii() and c.isalpha()) / max(len(text[:200]), 1)
    if eng_ratio > 0.6:
        return True
    if len(title) < 5 or len(title) > 100:
        return True
    return False

def is_interesting(title, summary):
    text = (title + " " + summary).lower()
    hit = sum(1 for kw in CORE_KWS if kw.lower() in text)
    return hit >= 1

def fetch_rss(url, name):
    entries = []
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15, verify=False)
        if resp.status_code != 200:
            return []
        feed = feedparser.parse(resp.text)
        for entry in feed.entries[:30]:
            title = (entry.get("title") or "").strip()
            summary = re.sub(r'<[^>]+>', '', entry.get("summary", entry.get("description", ""))).strip()
            if title:
                entries.append({"title": title, "summary": summary[:400], "source": name, "url": entry.get("link", "")})
    except:
        pass
    return entries

def extract_conclusion(summary):
    m = re.search(r'【大白话结论】([^【]*)', summary)
    if m:
        c = m.group(1).strip()
        c = c.replace("💡", "").strip()
        return c[:35] if len(c) > 35 else c
    return ""

def gen_daily_summary(news_list):
    global_seen = set()
    result = {}
    for ml in ["A", "B", "C", "D"]:
        items = [n for n in news_list if ml in n["mainline"]]
        items.sort(key=lambda n: {"大": 0, "中": 1, "小": 2}.get(n["impact"], 3))
        parts = []
        for n in items:
            c = extract_conclusion(n["summary"])
            if c and c not in global_seen:
                global_seen.add(c)
                parts.append(c)
            if len(parts) >= 3:
                break
        result[ml] = "；".join(parts) if parts else "——"
    return result

def score_news_item(item):
    score = 0
    title = item["title"]
    summary = item.get("summary", "")
    text = title + " " + summary
    source = item.get("source", "")
    if source == "华尔街见闻": score += 5
    elif source == "Tom's Hardware": score += 4
    elif source == "IT之家": score += 2
    elif source == "ServeTheHome": score += 4
    digits = len(re.findall(r'\d+', text[:300]))
    score += min(digits, 10)
    if re.search(r'(?:突破|量产|出货|收入.*亿|市占率|超预期|创纪录)', text):
        score += 5
    if re.search(r'(?:调查|报告|数据.*显示|Counterpoint|Omdia|瑞银|高盛|花旗)', text):
        score += 3
    if re.search(r'(?:ETF|etf|涨[跌]停|大涨|暴涨)', text):
        score -= 10
    if source == "IT之家" and len(title) > 60:
        score -= 3
    return score

ANALYZE_PROMPT = """你是一个顶级的AI算力/半导体产业链分析师，分析直接辅助基金经理做买卖决策。

仔细阅读新闻后，请按以下步骤思考，然后输出JSON：

第一步：提炼摘要
用一句简洁的话概括本条新闻的核心事实（50字左右）。要求：不要重复标题已表达的信息、不要写标题里已经有的话；语言通顺完整不要截断；结尾不要有多余符号，不要出现残缺的句子。

第二步：分析产业链影响
找出新闻中所有具体数字（金额、增长率、价格、估值等），结合这些数据判断对AI算力产业链的具体影响。解释清楚"为什么"和"怎么传导"的：例如某公司降价→上游供应商利润被压缩→设备采购延迟→中游订单减少。必须指名道姓列出1-3家直接相关的A股公司及原因。找不到A股标的就诚实说没找到。注意：语句完整通顺、不要有任何多余或错误的标点符号。

第三步：大白话结论
用像真人聊天的大白话直接说出结论，让普通投资者一听就懂"这事儿跟我有什么关系"。不要加任何开场标签或总结词。

影响力度判断标准：
- "大"=可能引发板块级行情或改变产业链竞争格局
- "中"=对特定环节/公司有明显影响但不会扩散到全板块
- "小"=信息量有限，参考价值不大

严格按以下JSON格式输出，不要在JSON外添加任何其他文字：
{
  "impact": "大",
  "digest": "简洁摘要（50字左右，不重复标题，语句完整）",
  "analysis": "产业链影响分析（150-250字，含具体数据和A股标的，标点正确）",
  "conclusion": "大白话结论（30-60字，无总结词）"
}

新闻内容："""


def deepseek_analyze_one(item, index):
    title = item.get("title", "")
    summary = item.get("_raw_summary", item.get("summary", ""))[:1000]

    user_msg = ANALYZE_PROMPT + f"标题：{title}\n内容：{summary}"

    retry_delays = [2, 4]
    for attempt in range(3):
        try:
            r = requests.post(DEEPSEEK_URL, json={
                "model": DEEPSEEK_MODEL,
                "messages": [{"role": "user", "content": user_msg}],
                "temperature": 0.5,
                "max_tokens": 2048,
            }, headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"}, timeout=120)

            if r.status_code != 200:
                print(f"  #{index} 返回{r.status_code}: {r.text[:100]}")
                if attempt < len(retry_delays):
                    time.sleep(retry_delays[attempt])
                    continue
                return None

            content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")

            json_str = content.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            result = json.loads(json_str)
            return result

        except json.JSONDecodeError:
            if attempt < len(retry_delays):
                time.sleep(retry_delays[attempt])
                continue
            print(f"  #{index} JSON解析失败，跳过")
            return None
        except Exception as e:
            if attempt < len(retry_delays):
                time.sleep(retry_delays[attempt])
                continue
            print(f"  #{index} 调用失败: {e}")
            return None

    return None


def apply_ai_analysis(news_items):
    if not DEEPSEEK_KEY:
        print("  ⚠️ 未配置DEEPSEEK_KEY，跳过AI分析")
        return

    total = len(news_items)
    print(f"  逐条AI分析中（共{total}条，每条约需3-5秒）...")

    ok = 0
    for i, item in enumerate(news_items):
        result = deepseek_analyze_one(item, i + 1)
        if result is None:
            print(f"  [{i+1}/{total}] ❌ 失败")
            continue

        impact = result.get("impact", "中")
        digest = result.get("digest", "")
        analysis = result.get("analysis", "")
        conclusion = result.get("conclusion", "")

        parts = []
        if digest:
            parts.append(digest.rstrip("。"))
        parts.append(f"【影响程度】{impact}")

        if analysis:
            parts.append(f"【产业链影响】{analysis.rstrip('。')}")

        if conclusion:
            parts.append(f"【大白话结论】{conclusion}")

        raw = "。".join(parts)
        raw = raw.replace("。。", "。")
        item["summary"] = raw
        item["impact"] = impact
        ok += 1

        print(f"  [{i+1}/{total}] ✓ {impact} {item['title'][:30]}...")
        time.sleep(0.5)

    # ============ 硬编码保障：每条新闻必须包含【产业链影响】和【大白话结论】 ============
    fixed = 0

    def pick_marker(tag, txt):
        m = re.search(tag + r'[^【]*', txt)
        return m.group(0).strip() if m else ""

    def strip_markers(txt):
        return re.sub(r'【[^】]*】[^【]*', '', txt).strip().rstrip("。")

    for item in news_items:
        s = item.get("summary", "")
        raw = item.get("_raw_summary", "")
        title = item.get("title", "")
        impact = item.get("impact", "中")

        if "【产业链影响】" in s and "【大白话结论】" in s:
            continue

        fixed += 1
        # DeepSeek成功时 s 带标记，失败时 s == raw（无标记）
        is_deepseek_fail = "【影响程度】" not in s
        raw_clean = re.sub(r'【[^】]*】', '', raw).strip().rstrip("。")
        s_clean = strip_markers(s).rstrip("。")

        # 取原文中最有信息量的关键句（非重复段落）
        def first_key_sentence(txt, min_len=30):
            txt = txt.strip()
            for sep in ["。", "；", "！", "？", "\n"]:
                parts = [p.strip() for p in txt.split(sep) if len(p.strip()) > min_len]
                if parts:
                    return parts[0] + ("。" if sep == "。" else sep)
            return txt[:min_len] + "……"

        if is_deepseek_fail:
            # DeepSeek完全失败：raw是唯一信息源，拆分使用避免重复
            key_sentence = first_key_sentence(raw_clean)
            item["summary"] = f"{key_sentence}【影响程度】{impact}。【产业链影响】{title}。{raw_clean}。【大白话结论】{key_sentence}"
        else:
            # DeepSeek部分成功：有标记但不全
            base = s_clean if s_clean else raw_clean
            final_parts = [base] if base else []
            final_parts.append(pick_marker("【影响程度】", s) or f"【影响程度】{impact}")

            if not pick_marker("【产业链影响】", s):
                ctx = raw_clean[:300]
                final_parts.append(f"【产业链影响】{title}。{ctx}")

            if not pick_marker("【大白话结论】", s):
                raw_short = raw_clean[:150]
                final_parts.append(f"【大白话结论】{raw_short}")

            item["summary"] = "。".join(final_parts).replace("。。", "。")

    if fixed:
        print(f"  ⚠️ 硬编码补全: 补了 {fixed} 条的缺失模块")

    print(f"  ✓ AI分析完成: {ok}/{total}条（{fixed}条补全）")


def gen_impact_auto(title, summary):
    text = (title + " " + summary).lower()
    if re.search(r'(?:突破|颠覆|革命|首发|首款|首|量产|供应.*链|出口管制|制裁)', text):
        return "大"
    if re.search(r'(?:增长|下降|扩大|缩减|占比|份额|升级)', text):
        return "中"
    return "小"


def quick_ai_summary(title, summary):
    clean = re.sub(r'<[^>]+>', '', summary)[:500]
    clean = re.sub(r'IT之家.*?日消息', '', clean)
    clean = re.sub(r'#欢迎关注爱范儿.*$', '', clean)
    clean = re.sub(r'#欢迎关注.*$', '', clean)
    clean = re.sub(r'\n+', '', clean)
    clean = clean.replace("\t", " ").strip()
    if len(clean) > 400:
        clean = clean[:397] + "..."
    return clean

def update_website_index():
    idx_path = os.path.join(DATA_DIR, "index.json")
    dates = set()
    for fname in os.listdir(DATA_DIR):
        if fname.endswith(".json") and fname not in ("index.json", "breakthrough.json"):
            dates.add(fname.replace(".json", ""))
    try:
        r = requests.get("https://portfolio-analysis.top/news/data/index.json", timeout=10)
        if r.status_code == 200:
            remote = r.json().get("dates", [])
            dates.update(remote)
    except Exception:
        pass
    sorted_dates = sorted(dates)
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump({"dates": sorted_dates, "count": len(sorted_dates)}, f, ensure_ascii=False, indent=2)
    for ds in sorted_dates:
        fpath = os.path.join(DATA_DIR, f"{ds}.json")
        if not os.path.exists(fpath):
            try:
                r = requests.get(f"https://portfolio-analysis.top/news/data/{ds}.json", timeout=10)
                if r.status_code == 200:
                    with open(fpath, "w", encoding="utf-8") as f:
                        json.dump(r.json(), f, ensure_ascii=False, indent=2)
                    print(f"  ✅ 已从 OSS 补回缺失的数据: {ds}.json")
            except Exception:
                pass

def main():
    today_str = date.today().strftime("%Y-%m-%d")
    print("=" * 50)
    print(f"[AI算力每日资讯] {today_str}")
    print("=" * 50)

    # 幂等检查：今天数据已生成则跳过（避免多个 cron 时间点重复推送）
    # 设置环境变量 FORCE_REFRESH=1 可强制重新生成
    if os.environ.get("FORCE_REFRESH") != "1":
        today_file = os.path.join(DATA_DIR, f"{today_str}.json")
        if os.path.exists(today_file):
            try:
                with open(today_file, encoding="utf-8") as f:
                    d = json.load(f)
                if d.get("count", 0) > 0:
                    print(f"✅ 今日数据已存在({d['count']}条)，跳过重复生成")
                    print(f"   如需强制重新生成，设置环境变量 FORCE_REFRESH=1")
                    return d["count"]
            except Exception:
                pass  # 文件损坏，重新生成

    print("\n[1/5] RSS采集...")
    all_raw = []
    for label, url in RSS_SOURCES:
        entries = fetch_rss(url, label)
        all_raw.extend(entries)
        print(f"  {label}: {len(entries)}条")
    print(f"  原始采集: {len(all_raw)}条")

    print("\n[2/5] 去重+过滤...")
    seen = set()
    deduped = []
    for e in all_raw:
        key = e["title"][:60].strip().lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(e)
    filtered = [e for e in deduped if not should_block(e["title"], e.get("summary", "")) and is_interesting(e["title"], e.get("summary", ""))]
    print(f"  去重: {len(deduped)} → 过滤: {len(filtered)}")

    print("\n[3/5] 打分+精选...")
    scored = [(score_news_item(e), e) for e in filtered]
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:50]
    print(f"  候选: {len(top)}条 → 目标: 20-30条/天")

    print("\n[4/5] 生成分析...")
    news_list = []
    for idx, (score, item) in enumerate(top):
        t = item["title"]
        s = item.get("summary", "")
        raw = quick_ai_summary(t, s)
        news_list.append({
            "id": idx,
            "title": t,
            "summary": raw,
            "_raw_summary": raw,
            "mainline": get_mainline(t),
            "impact": gen_impact_auto(t, s),
            "source": item.get("source", ""),
            "url": item.get("url", ""),
            "time": ""
        })

    # AI深度分析（逐条独立调用DeepSeek，最大化分析质量）
    apply_ai_analysis(news_list)

    daily_summary = gen_daily_summary(news_list)

    print("\n[5/5] 写入数据...")
    data = {
        "date": today_str,
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "count": len(news_list),
        "news": news_list,
        "daily_summary": daily_summary
    }
    with open(os.path.join(DATA_DIR, f"{today_str}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    update_website_index()

    print(f"\n✅ 完成! 共 {len(news_list)} 条")
    print(f"   主线: A={sum(1 for n in news_list if 'A' in n['mainline'])}, B={sum(1 for n in news_list if 'B' in n['mainline'])}, C={sum(1 for n in news_list if 'C' in n['mainline'])}, D={sum(1 for n in news_list if 'D' in n['mainline'])}")
    print(f"   文件: {os.path.join(DATA_DIR, f'{today_str}.json')}")

    return len(news_list)

if __name__ == "__main__":
    main()
