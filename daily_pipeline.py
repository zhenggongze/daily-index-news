#!/usr/bin/env python3
"""
AI算力产业链每日资讯 全自动流水线 v3
流程：RSS采集 → 去重 → LLM批量分类(20-shot prompt) → 只对相关新闻逐条深度分析 → 写入JSON
目标产出：10-25条/天高质量新闻，cron-job.org 每天 08:07 触发
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
    ("36氪8点1氪", "https://36kr.com/feed"),
    ("量子位", "https://www.qbitai.com/feed"),
    ("雷锋网", "https://www.leiphone.com/feed"),
    ("InfoQ", "https://www.infoq.cn/feed"),
    ("钛媒体", "https://www.tmtpost.com/rss.xml"),
    ("IEEE Spectrum", "https://spectrum.ieee.org/feeds/type/news.rss"),
    ("SemiconductorEngineering", "https://semiengineering.com/feed"),
    ("SemiWiki", "https://semiwiki.com/feed"),
    ("Phoronix", "https://www.phoronix.com/rss.php"),
    ("Tom's Hardware", "https://www.tomshardware.com/feeds/all"),
    ("ServeTheHome", "https://www.servethehome.com/feed"),
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

def fetch_rss(url, name):
    entries = []
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30, verify=False)
        if resp.status_code != 200:
            print(f"    {name}: HTTP {resp.status_code}")
            return []
        feed = feedparser.parse(resp.text)
        count = len(feed.entries)
        for entry in feed.entries[:30]:
            title = (entry.get("title") or "").strip()
            summary = re.sub(r'<[^>]+>', '', entry.get("summary", entry.get("description", ""))).strip()
            if title:
                entries.append({"title": title, "summary": summary[:400], "source": name, "url": entry.get("link", "")})
        status = f"✅ {count}条" if count > 0 else f"⚠️ 0条 (可能非RSS或解析失败)"
        print(f"    {name}: {status}")
    except Exception as e:
        print(f"    {name}: ❌ {type(e).__name__}: {str(e)[:80]}")
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

CLASSIFY_PROMPT = """你是一个顶级AI算力/半导体产业链分析师。逐条判断以下新闻是否与 AI算力产业链投资 直接相关。

每一条新闻必须输出一个JSON对象（字段见末尾），必须逐条对应，不要合并或跳过。

==== 相关性判断标准 ====

relevant=true（相关）— 以下任一情况：
1. AI算力硬件本身：芯片/GPU/CPU/NPU/TPU/LPU/存储芯片/HBM/DRAM/NAND/DDR5/光模块/PCB/液冷/散热/服务器/CoWoS/先进封装/半导体设备/半导体材料/晶圆代工/制程/EUV/刻蚀/薄膜/数据中心
2. AI模型或平台重大突破：大模型发布/推理性能重大提升/训练成本大幅下降/头部公司（OpenAI/Anthropic/Google/智谱/DeepSeek/字节豆包）发布能改变算力需求格局的产品
3. AI产业链头部公司战略转向或重大投资：英伟达/台积电/SK海力士/美光/三星/鸿海/华为（AI方向）/字节（AI方向）/OpenAI—涉及AI算力的产线扩产/削减/并购/战略调整/资本开支
4. 机构对AI板块的明确投资研判：券商/投行/基金对AI算力板块（芯片/光模块/存储/服务器/液冷）的研报或持仓分析
5. AI电力/能源基础设施：数据中心用核能/天然气/电力协议——直接影响算力成本或供给
6. AI对半导体上游原材料的需求信号：如六氟化钨/铟/氮化铝/金刚石等关键材料供需紧张

relevant=false（不相关）— 以下任一情况：
1. 消费电子：手机（含折叠屏）/平板/手表/耳机/音箱/手环/笔记本（除非内容明确讨论AI PC芯片）
2. 汽车：自动驾驶车型交付/发布/价格调整（除非内容明确讨论自动驾驶芯片或AI训练）
3. 人事/组织：公司聘用/离任/退休/组织架构调整/人事任命
4. 慈善/捐款/公益/社会责任
5. 媒体评论/喊话：如"央视评XX""人民日报XX"——无实质产业链信息
6. 招聘：公司发布的招聘信息（即使是AI公司）
7. 产品外观曝光/谍照/渲染图
8. 操作系统/App更新（与AI硬件产业链无关）
9. 纯消费级产品发布：如电视/空调/冰箱/扫地机器人/数据线
10. 排行榜/盘点/汇总类文章
11. 与半导体/AI产业链无关的公司行为
12. 支付/银行卡/银联类新闻
13. 无人机/相机等硬件（与AI芯片/算力无关）
14. 纯科普/环境/碳足迹文章（无具体公司或数据）

impact判断标准（仅relevant=true时填 大/中/小；relevant=false时填"无"）：
- "大"：可能引发板块级行情或改变产业链竞争格局，影响量级达数亿元以上；或属于能显著改变产业链竞争格局、强化/削弱龙头地位的战略级信号
- "中"：对特定环节/公司有实质性影响，量级千万~亿元
- "小"：信息量有限，参考价值不大

==== 示例（严谨参照）====

示例1 — 相关(大)：
标题：台积电宣布2nm工艺2026年Q1量产，产能已被苹果英伟达预订一空
相关：true | 影响：大
理由：先进制程重大突破

示例2 — 相关(大)：
标题：英伟达发布Rubin Ultra GPU，AI训练性能提升4倍
相关：true | 影响：大
理由：旗舰GPU换代，重新定义算力格局

示例3 — 相关(大)：
标题：美商务部新增对华AI芯片出口管制清单
相关：true | 影响：大
理由：出口管制板块级冲击

示例4 — 相关(大)：
标题：字节跳动新设"算力基建部"直管AI算力采购
相关：true | 影响：大
理由：字节算力战略转向，涉及GPU/光模块大规模采购

示例5 — 相关(大)：
标题：当台积电三星SK海力士都在抢货，电子级氢氟酸成为AI芯片制造不可替代的"化学钥匙"
相关：true | 影响：大
理由：新材料替代+A股直接供应商，订单量级数亿元

示例6 — 相关(中)：
标题：SK海力士清州工厂订购逾200台HBM4测试仪，总价4000亿韩元
相关：true | 影响：中
理由：HBM4设备采购量级可观

示例7 — 相关(中)：
标题：中际旭创预计Q3营收同比增长180%，800G光模块出货超预期
相关：true | 影响：中
理由：光模块龙头业绩超预期

示例8 — 相关(小)：
标题：三星1.4nm工艺或将于2029年重启量产
相关：true | 影响：小
理由：时间线太远(2029年)，无实质影响

示例9 — 不相关：
标题：Omdia：2026年Q1三星折叠面板份额降至27%
相关：false
理由：折叠面板是消费电子

示例10 — 不相关：
标题：小米REDMI K90至尊版手机发布：骁龙8至尊版+主动散热风扇，首销到手价2799元起
相关：false
理由：手机发布，消费电子

示例11 — 不相关：
标题：央视评寒武纪市值破万亿：更需一份清醒定力
相关：false
理由：媒体评论喊话，无产业链信息

示例12 — 不相关：
标题：美光科技宣布投入2.5亿美元助力百万儿童储蓄
相关：false
理由：慈善行为，非产业动态

示例13 — 不相关：
标题：深开鸿KaihongOS桌面版V5.0.2.30更新上线
相关：false
理由：操作系统小版本更新

示例14 — 不相关：
标题：大疆无人机DJI Fly鸿蒙版App正式上架华为应用市场
相关：false
理由：无人机App上架，与算力无关

示例15 — 不相关：
标题：银联推出AI智算卡：银行卡开始「外挂」大模型
相关：false
理由：银行卡金融产品，与算力无关

示例16 — 不相关：
标题：AI能源使用的环境成本：碳足迹、水足迹与土地足迹
相关：false
理由：科普文章，无具体公司或数据

示例17 — 不相关：
标题：华为官宣全球首个商用多模态文旅大模型规模化应用，衍生品销售200万元
相关：false
理由：项目规模太小(营收仅200万)，可忽略

示例18 — 不相关：
标题：对比鲜明！美股创"六年来最佳一季"，黄金经历"十多年来最差一季"
相关：false
理由：社会共识/公开已知信息，无增量投资价值

示例19 — 不相关：
标题：寒武纪万亿市值夜的"冷水"：上游涨价挤压利润
相关：false
理由：公司自身风险提示公告，非实质变化

示例20 — 不相关：
标题：近一年收益220%，汇丰晋信陈平：AI算力中最看好光模块
相关：false
理由：基金经理主观观点，无新增数据

==== 待分类新闻列表 ====

输出格式（JSON数组，每条对应一条输入新闻）：
[
  {"idx":0,"relevant":true,"impact":"大","reason":"简短理由≤15字"},
  {"idx":1,"relevant":false,"impact":"无","reason":"简短理由≤15字"},
  ...
]

输入新闻："""

def llm_classify_batch(candidates):
    if not candidates or not DEEPSEEK_KEY:
        return []

    CHUNK_SIZE = 50
    all_results = []
    total = len(candidates)

    for chunk_start in range(0, total, CHUNK_SIZE):
        chunk = candidates[chunk_start:chunk_start + CHUNK_SIZE]
        lines = []
        for i, item in enumerate(chunk):
            global_idx = chunk_start + i
            t = item["title"]
            s = item.get("summary", "")[:200]
            lines.append(f"idx={global_idx} | 标题：{t}\n摘要：{s}")

        user_msg = CLASSIFY_PROMPT + "\n\n---\n\n".join(lines)
        progress = f"{chunk_start + 1}-{min(chunk_start + len(chunk), total)}/{total}"
        print(f"  LLM批量分类 {progress}（{len(chunk)}条）...")

        chunk_ok = False
        retry_delays = [2, 4]
        for attempt in range(3):
            try:
                r = requests.post(DEEPSEEK_URL, json={
                    "model": DEEPSEEK_MODEL,
                    "messages": [{"role": "user", "content": user_msg}],
                    "temperature": 0.2,
                    "max_tokens": 8192,
                }, headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"}, timeout=180)

                if r.status_code != 200:
                    if attempt < 2:
                        time.sleep(retry_delays[attempt])
                        continue
                    print(f"    ⚠️ HTTP {r.status_code}: {r.text[:100]}")
                    break

                content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                json_str = content.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()
                bracket = json_str.find("[")
                end = json_str.rfind("]")
                if bracket >= 0 and end > bracket:
                    json_str = json_str[bracket:end+1]

                results = json.loads(json_str)
                if isinstance(results, list):
                    rel = sum(1 for r in results if r.get("relevant"))
                    all_results.extend(results)
                    print(f"    ✅ 相关 {rel}/{len(results)}")
                    chunk_ok = True
                    break
                if attempt < 2:
                    time.sleep(retry_delays[attempt])
                    continue
                print(f"    ⚠️ 分类结果非数组")
                break
            except json.JSONDecodeError:
                if attempt < 2:
                    time.sleep(retry_delays[attempt])
                    continue
                print(f"    ⚠️ JSON解析失败")
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(retry_delays[attempt])
                    continue
                print(f"    ⚠️ 调用失败: {e}")
                break

        if not chunk_ok:
            for i in range(len(chunk)):
                all_results.append({"idx": chunk_start + i, "relevant": False, "impact": "无", "reason": "分类超时"})

    rel_count = sum(1 for r in all_results if r.get("relevant"))
    print(f"  分类完成：相关 {rel_count} 条 / 总计 {len(all_results)} 条")
    return all_results

ANALYZE_PROMPT = """你是一个顶级的AI算力/半导体产业链分析师，分析直接辅助基金经理做买卖决策。

仔细阅读新闻后，请按以下步骤思考，然后输出JSON：

第一步：提炼摘要
用一句简洁的话概括本条新闻的核心事实（50字左右）。要求：不要重复标题已表达的信息、不要写标题里已经有的话；语言通顺完整不要截断；结尾不要有多余符号，不要出现残缺的句子。

第二步：分析产业链影响
找出新闻中所有具体数字（金额、增长率、价格、估值等），结合这些数据判断对AI算力产业链的具体影响。解释清楚"为什么"和"怎么传导"的：例如某公司降价→上游供应商利润被压缩→设备采购延迟→中游订单减少。必须指名道姓列出1-3家直接相关的A股公司及原因。找不到A股标的就诚实说没找到。注意：语句完整通顺、不要有任何多余或错误的标点符号。

第三步：大白话结论
用像真人聊天的大白话直接说出结论，让普通投资者一听就懂"这事儿跟我有什么关系"。不要加任何开场标签或总结词。

影响力度判断标准：
- "大"=可能引发板块级行情或改变产业链竞争格局，影响量级达数亿元以上；
  或虽无法量化具体营收，但属于能显著改变产业链竞争格局、强化/削弱龙头地位的
  战略级信号（如关键技术创新、颠覆性产品发布、头部公司重大转向）
- "中"=对特定环节/公司有实质性影响，影响量级达千万~亿元，能对公司季度营收产生可辨识变化，但不会扩散到全板块
- "小"=信息量有限，参考价值不大；或虽有相关标的，但影响量级在千万以下、相对公司体量可忽略

关键原则（必须遵守）：
1. 社会共识/公开已知信息 → 一律判"小"：如"AI涨了很多""美股芯片大涨""存储很火"等市场已反复讨论且股价已反映的信息，属于人人皆知的共识，归为"小"甚至应判不相关。
2. 基金经理/分析师主观观点（无新增数据） → 一律判"小"：个人观点、喊话、展望，不包含订单/产量/营收等客观产业链数据。
3. 机构警告/喊话（无具体数据支撑） → 一律判"小"：IMF/投行等风险警告，不包含具体数字的均判"小"。
4. 公司自身风险提示/常规公告 → 一律判"小"：非高管减持/业绩预警/订单丢失的常规披露，判"小"。
5. 新材料替代且有A股直接供应关系 → 优先判"大"或"中"：如电子级氢氟酸供货台积电、多氟多等直接受益，订单量级可达数亿元，应判"大"。
6. 已发生在海外的行情（非A股） → 一律判"小"：欧洲/美股大盘涨跌、全球宏观行情，即使提到AI，与A股投资决策无直接关联。

判断影响力度前，优先估算该事件对相关A股公司营收/利润的影响量级。
若无法量化具体营收，则判断该事件是否属于能改变产业链竞争格局的战略级信号。

严格按以下JSON格式输出，不要在JSON外添加任何其他文字：
{
  "impact": "大",
  "digest": "简洁摘要（50字左右，不重复标题，语句完整）",
  "analysis": "产业链影响分析（150-250字，含具体数据和A股标的，标点正确）",
  "conclusion": "大白话结论（30-60字，无总结词）"
}

新闻内容："""


def enrich_short_summary(title, raw_summary, url):
    """若原始摘要<300字，尝试从文章URL获取完整内容补充"""
    if not raw_summary or len(raw_summary) >= 300:
        return raw_summary
    if not url:
        return raw_summary
    try:
        resp = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        if resp.status_code != 200:
            return raw_summary
        text = re.sub(r'<[^>]+>', ' ', resp.text)
        text = re.sub(r'\s+', ' ', text).strip()
        enriched = text[:3000] if len(text) > len(raw_summary) else raw_summary
        if len(enriched) > len(raw_summary):
            print(f"  原始摘要过短({len(raw_summary)}字)，已从URL补充至{len(enriched)}字")
            return enriched
        return raw_summary
    except Exception:
        return raw_summary


def deepseek_analyze_one(item, index):
    title = item.get("title", "")
    raw = item.get("_raw_summary", item.get("summary", ""))
    url = item.get("url", "")
    raw = enrich_short_summary(title, raw, url)
    summary = raw[:1000]

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
    failed_items = []
    for i, item in enumerate(news_items):
        result = deepseek_analyze_one(item, i + 1)
        if result is None:
            print(f"  [{i+1}/{total}] ❌ 失败")
            failed_items.append(item)
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

    for item in failed_items:
        item["_deepseek_fully_failed"] = True

    print(f"  ✓ AI分析完成: {ok}/{total}条（{fixed}条补全）")


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

def load_recent_seen(days=7):
    """从 OSS 拉取最近 days 天的数据文件，建立已采集的 URL 和标题集合（用于跨日去重）
    注意：排除今天，避免重新生成时把自己也去重"""
    today_str = date.today().strftime("%Y-%m-%d")
    seen_urls = set()
    seen_titles = set()
    base = "https://portfolio-analysis.top/news/data"
    try:
        r = requests.get(f"{base}/index.json", timeout=10)
        if r.status_code != 200:
            return seen_urls, seen_titles
        all_dates = r.json().get("dates", [])
    except Exception:
        return seen_urls, seen_titles

    # 只取最近 days 天，但排除今天（避免重新生成时把自己去重）
    recent = [d for d in sorted(all_dates, reverse=True) if d != today_str][:days]
    for ds in recent:
        try:
            r = requests.get(f"{base}/{ds}.json", timeout=10)
            if r.status_code != 200:
                continue
            news = r.json().get("news", [])
            for n in news:
                u = (n.get("url") or "").strip()
                t = (n.get("title") or "").strip().lower()
                if u:
                    seen_urls.add(u)
                if t:
                    seen_titles.add(t)
        except Exception:
            continue
    print(f"  跨日去重: 加载最近 {len(recent)} 天数据，已有 {len(seen_urls)} 个URL、{len(seen_titles)} 个标题")
    return seen_urls, seen_titles


def is_dup_cross_day(item, seen_urls, seen_titles):
    """URL 完全匹配 或 标题完全匹配 → 判定为跨日重复"""
    u = (item.get("url") or "").strip()
    t = (item.get("title") or "").strip().lower()
    if u and u in seen_urls:
        return True
    if t and t in seen_titles:
        return True
    return False


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

TITLE_REWRITE_PROMPT = """你是一个中文新闻标题编辑。将以下新闻标题处理成适合AI算力产业链投资者阅读的中文标题。

规则：
1. 完整日早报/晚报/早餐FM类标题 → 提取其中与AI算力产业链直接相关的核心事件作为新标题，不保留"IT早报""早餐FM"前缀
2. 纯英文标题 → 翻译为简洁中文
3. 标题中若包含多个子事件（用分隔符隔开） → 只保留与AI算力/半导体/芯片直接相关的事件
4. 处理后的标题长度不超过40个中文字符
5. 保持客观，不加主观评价

输出格式（JSON数组，与输入一一对应）：
[
  {"idx":0,"title":"处理后标题"},
  {"idx":1,"title":"处理后标题"},
  ...
]

输入新闻："""

def rewrite_titles(news_list):
    if not news_list or not DEEPSEEK_KEY:
        return
    # 只处理需要改写的标题：含"IT早报""早餐FM""FM-Radio"的，或含较多英文的
    need_rewrite_idx = []
    for i, item in enumerate(news_list):
        t = item["title"]
        if any(kw in t for kw in ["IT早报", "早餐", "FM-Radio", "FM |"]):
            need_rewrite_idx.append(i)
        elif re.search(r'[A-Za-z]{3,}', t):
            eng_ratio = sum(1 for c in t[:100] if c.isascii() and c.isalpha()) / max(len(t[:100]), 1)
            if eng_ratio > 0.15:
                need_rewrite_idx.append(i)
    if not need_rewrite_idx:
        return

    print(f"  改写 {len(need_rewrite_idx)} 条标题...")
    lines = [f"idx={i} | 原始标题：{news_list[i]['title']}" for i in need_rewrite_idx]
    user_msg = TITLE_REWRITE_PROMPT + "\n\n---\n\n".join(lines)

    for attempt in range(3):
        try:
            r = requests.post(DEEPSEEK_URL, json={
                "model": DEEPSEEK_MODEL,
                "messages": [{"role": "user", "content": user_msg}],
                "temperature": 0.2,
                "max_tokens": 4096,
            }, headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"}, timeout=120)

            if r.status_code != 200:
                if attempt < 2:
                    time.sleep(2)
                    continue
                return

            content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            json_str = content.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            bracket = json_str.find("[")
            end = json_str.rfind("]")
            if bracket >= 0 and end > bracket:
                json_str = json_str[bracket:end+1]

            results = json.loads(json_str)
            if isinstance(results, list):
                for result in results:
                    idx = result.get("idx", -1)
                    new_title = result.get("title", "")
                    if idx >= 0 and idx < len(need_rewrite_idx) and new_title:
                        orig_idx = need_rewrite_idx[idx]
                        old_title = news_list[orig_idx]["title"]
                        if old_title != new_title:
                            news_list[orig_idx]["title"] = new_title
                            print(f"    {old_title[:30]}... → {new_title}")
                return
        except Exception:
            if attempt < 2:
                time.sleep(2)
                continue
            return

def main():
    today_str = date.today().strftime("%Y-%m-%d")
    print("=" * 50)
    print(f"[AI算力每日资讯] {today_str}")
    print("=" * 50)

    # 幂等检查：先查 OSS 远端是否有今天数据，有则跳过（即使 FORCE_REFRESH=1 也跳过，避免重复推送）
    today_url = f"https://portfolio-analysis.top/news/data/{today_str}.json"
    try:
        resp = requests.get(today_url, timeout=10, verify=False)
        if resp.status_code == 200:
            d = resp.json()
            if d.get("count", 0) > 0:
                print(f"✅ OSS 已有今日数据({d['count']}条)，跳过重复生成")
                return d["count"]
    except Exception:
        pass  # OSS 无数据，正常生成

    # 再尝试本地文件
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

    print("\n[2/5] 去重...")
    seen_urls, seen_titles = load_recent_seen(days=7)
    cross_day_dup = 0

    seen = set()
    deduped = []
    for e in all_raw:
        t = e["title"]
        s = e.get("summary", "")
        raw = quick_ai_summary(t, s)
        e["_raw"] = raw
        key = e["title"][:60].strip().lower()
        if key and key not in seen:
            seen.add(key)
            if is_dup_cross_day(e, seen_urls, seen_titles):
                cross_day_dup += 1
                continue
            deduped.append(e)
    print(f"  跨日重复剔除: {cross_day_dup} 条")
    print(f"  去重后候选: {len(deduped)} 条")

    print("\n[3/5] LLM批量分类（判断相关性+影响度）...")
    classifications = llm_classify_batch(deduped)

    news_list = []
    dropped = []
    for cl in classifications:
        idx = cl.get("idx", -1)
        if idx < 0 or idx >= len(deduped):
            continue
        if not cl.get("relevant", False):
            reason = cl.get("reason", "")
            dropped.append(f"{deduped[idx]['title'][:30]}... ({reason})")
            continue
        item = deduped[idx]
        news_list.append({
            "id": len(news_list),
            "title": item["title"],
            "summary": item["_raw"],
            "_raw_summary": item["_raw"],
            "mainline": get_mainline(item["title"]),
            "impact": cl.get("impact", "中"),
            "source": item.get("source", ""),
            "url": item.get("url", ""),
            "time": ""
        })

    if dropped:
        print(f"  LLM过滤不相关: {len(dropped)} 条")
        for t in dropped[:10]:
            print(f"    ✂️ {t}")
        if len(dropped) > 10:
            print(f"    ... 还有 {len(dropped)-10} 条")
    print(f"  LLM判定相关: {len(news_list)} 条")

    # 兜底：相关过少时从高分源补充
    if len(news_list) < 8 and len(classifications) > 0:
        print(f"  ⚠️ 相关不足8条，从高分源补充...")
        for cl in classifications:
            idx = cl.get("idx", -1)
            if idx < 0 or idx >= len(deduped):
                continue
            if cl.get("relevant", False):
                continue
            item = deduped[idx]
            if item.get("source") in ["华尔街见闻", "ServeTheHome", "Tom\'s Hardware"]:
                news_list.append({
                    "id": len(news_list),
                    "title": item["title"],
                    "summary": item["_raw"],
                    "_raw_summary": item["_raw"],
                    "mainline": get_mainline(item["title"]),
                    "impact": "小",
                    "source": item.get("source", ""),
                    "url": item.get("url", ""),
                    "time": ""
                })
                if len(news_list) >= 8:
                    break
        print(f"  补充后: {len(news_list)} 条")

    print("\n[4/5] 逐条深度分析...")

    if not news_list:
        print("  ⚠️ 无相关新闻，跳过")
        return 0

    apply_ai_analysis(news_list)

    # 移除DeepSeek分析完全失败的条目（如内容过长导致JSON解析失败）
    before = len(news_list)
    news_list = [n for n in news_list if not n.get("_deepseek_fully_failed", False)]
    if len(news_list) < before:
        print(f"  🗑️ 移除 {before - len(news_list)} 条分析失败项")

    # 改写标题：IT早报/早餐FM提取核心事件 + 英文标题翻译中文
    rewrite_titles(news_list)

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
