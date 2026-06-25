"""
种子数据生成脚本
将 news_50_v4.txt 中的50条新闻导入网站JSON格式
"""
import sys, os, re, json

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "news_site"))
os.chdir(os.path.join(BASE, "news_site"))
from update_news import manual_add, write_daily_json, detect_mainline, detect_impact

NEWS_SRC = os.path.join(BASE, "news_50_v4.txt")

def parse_v4_news():
    """解析news_50_v4.txt格式"""
    items = []
    with open(NEWS_SRC, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_title = ""
    current_summary = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip header
        if line.startswith("标题\t") or line == "标题":
            continue

        parts = line.split("\t")
        if len(parts) >= 2:
            # New entry
            if current_title:
                items.append({"title": current_title, "summary": current_summary})
            current_title = parts[0].strip()
            current_summary = parts[1].strip() if len(parts) > 1 else ""
        elif current_title:
            current_summary += " " + line

    if current_title:
        items.append({"title": current_title, "summary": current_summary})

    print(f"解析到 {len(items)} 条新闻")
    return items

# 主线标注知识库（对照每条新闻人工修正）
MAINLINE_MAP = {
    "智谱": "A, D",
    "三星HBM": "B",
    "谷歌TPU": "B, D",
    "上海超硅": "A",
    "鸿海": "B",
    "存储芯片市场": "B",
    "韩国芯片出口": "B",
    "铟价": "B",
    "氮化铝": "B",
    "OpenAI": "D",
    "ChatGPT": "D",
    "三星向员工": "D",
    "英伟达Rubin.*液冷": "B",
    "中国AI模型训练成本": "A, D",
    "AI Agent.*CPU": "D",
    "AI PCB": "B",
    "金刚石散热": "B",
    "SK海力士市值": "B",
    "花旗看高美光": "B",
    "电容成AI": "B",
    "SpaceX上市": "D",
    "皮尤调查": "D",
    "员工已用AI工具": "D",
    "黄仁勋链博会": "B",
    "华为鸿蒙": "A",
    "苹果加价锁定": "D",
    "字节跳动洽购": "A, D",
    "英特尔前海力士": "B",
    "AI推理加速向私有化": "D",
    "OpenAI Codex": "D",
    "Isaac Sim": "C",
    "华为PC出货": "A",
    "三星DS部门": "A",
    "Anthropic F5": "A, D",
    "ACE指令集": "B",
    "骁龙X2": "B",
    "全球手机降8%": "A",
    "宁德时代": "D",
    "FERC": "D",
    "Sanders提案": "D",
    "P5 Fab 2": "B",
    "Rubin机架单价": "B",
    "链博会首设AI": "D",
    "Agent激增": "D",
    "金刚石.*液冷": "B",
    "芯片出口连涨": "B",
    "低成本优势.*华尔街": "A, D",
    "存储三巨头": "B",
}

def get_mainline(title):
    for kw, ml in MAINLINE_MAP.items():
        if kw.lower() in title.lower():
            return ml
    return detect_mainline(title, "")

if __name__ == "__main__":
    items = parse_v4_news()

    # 构建带完整字段的新闻列表
    news_list = []
    for i, item in enumerate(items):
        title = item["title"]
        summary = item["summary"]
        mainline = get_mainline(title)
        impact = detect_impact(summary)
        news_list.append({
            "title": title,
            "summary": summary,
            "mainline": mainline,
            "impact": impact,
            "source": "精选",
            "time": ""
        })

    # 写入2026-06-22的JSON
    result = write_daily_json(news_list, "2026-06-22")

    # 同时再写一份今天的，方便测试
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    if today != "2026-06-22":
        write_daily_json(news_list, today)

    print(f"✅ 种子数据导入完成！")
    print(f"   共 {len(news_list)} 条新闻")
    print(f"   打开 news_site/index.html 即可查看")
