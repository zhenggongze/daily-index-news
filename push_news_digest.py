#!/usr/bin/env python3
"""
推送今日 AI算力产业链资讯摘要到 PushDeer
读取 daily_pipeline.py 生成并部署到 OSS 的 news JSON，按影响级别分组推送。

用法：
  python push_news_digest.py
  python push_news_digest.py --date 2026-06-24   # 指定日期（调试用）
"""
import os, sys, json, re, time, requests
from datetime import date, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "news_site", "public", "data")

PUSHDEER_KEY = os.environ.get("PUSHDEER_KEY", "")
PUSHDEER_URL = "https://api2.pushdeer.com/message/push"
PUSH_TITLE = "AI算力产业链每日资讯"
SITE_URL = "https://portfolio-analysis.top/news/index.html"

# 主线标签
MAINLINE_LABEL = {
    "A": "半导体材料/设备",
    "B": "服务器/存储/光模块",
    "C": "机器人/具身智能",
    "D": "AI应用/大模型",
}


def load_today_news(target_date):
    """读取指定日期的 news JSON"""
    path = os.path.join(DATA_DIR, f"{target_date}.json")
    if not os.path.exists(path):
        print(f"  ⚠️ 文件不存在: {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  ⚠️ 读取失败: {e}")
        return None


def extract_conclusion(summary):
    """从 summary 中提取【大白话结论】"""
    m = re.search(r'【大白话结论】([^【]*)', summary)
    if m:
        c = m.group(1).strip().rstrip("。")
        return c[:80] if len(c) > 80 else c
    return ""


def build_digest_md(data):
    """把 news JSON 整理成 PushDeer markdown 摘要"""
    news_list = data.get("news", [])
    if not news_list:
        return None

    today_str = data.get("date", "")
    try:
        dt = datetime.strptime(today_str, "%Y-%m-%d")
        date_label = f"{dt.year}年{dt.month}月{dt.day}日"
    except Exception:
        date_label = today_str

    # 按 impact 分组
    groups = {"大": [], "中": [], "小": []}
    for n in news_list:
        impact = n.get("impact", "中")
        if impact not in groups:
            impact = "中"
        groups[impact].append(n)

    lines = [f"# 📊 {PUSH_TITLE}", f"## 📅 {date_label}", ""]

    # 影响大
    if groups["大"]:
        lines.append(f"### 🔥 影响大（{len(groups['大'])}条）")
        lines.append("")
        for i, n in enumerate(groups["大"], 1):
            title = n.get("title", "")[:60]
            conclusion = extract_conclusion(n.get("summary", ""))
            ml = MAINLINE_LABEL.get(n.get("mainline", ""), "")
            lines.append(f"**{i}. {title}**")
            if ml:
                lines.append(f"<sub>{ml}</sub>")
            if conclusion:
                lines.append(f"> {conclusion}")
            lines.append("")

    # 影响中
    if groups["中"]:
        lines.append(f"### ⚡ 影响中（{len(groups['中'])}条）")
        lines.append("")
        for i, n in enumerate(groups["中"], 1):
            title = n.get("title", "")[:60]
            conclusion = extract_conclusion(n.get("summary", ""))
            ml = MAINLINE_LABEL.get(n.get("mainline", ""), "")
            lines.append(f"**{i}. {title}**")
            if ml:
                lines.append(f"<sub>{ml}</sub>")
            if conclusion:
                lines.append(f"> {conclusion}")
            lines.append("")

    # 影响小只列数量
    if groups["小"]:
        lines.append(f"### 📌 影响小（{len(groups['小'])}条，详见网站）")
        lines.append("")

    lines.append("---")
    lines.append(f"🌐 完整内容：{SITE_URL}")
    lines.append(f"📊 共 {len(news_list)} 条 | 大{len(groups['大'])} 中{len(groups['中'])} 小{len(groups['小'])}")

    return "\n".join(lines)


def push_to_pushdeer(content):
    """推送到 PushDeer，3次重试"""
    if not PUSHDEER_KEY:
        print("  ⚠️ 未配置 PUSHDEER_KEY，跳过推送")
        return False
    if not content:
        print("  ⚠️ 内容为空，跳过推送")
        return False

    for attempt in range(1, 4):
        try:
            r = requests.post(PUSHDEER_URL, data={
                "pushkey": PUSHDEER_KEY,
                "text": PUSH_TITLE,
                "type": "markdown",
                "desp": content,
            }, timeout=30)
            j = r.json()
            if j.get("code") == 0:
                print("  ✅ PUSH_SUCCESS")
                return True
            print(f"  ❌ PUSH_FAILED({attempt}): {j.get('error', 'unknown')}")
        except Exception as e:
            print(f"  ❌ REQUEST_ERROR({attempt}): {e}")
        if attempt < 3:
            time.sleep(3)
    print("  ❌ PUSH_FAILED: max_retries_exceeded")
    return False


def main():
    # 解析日期参数
    target_date = date.today().isoformat()
    if len(sys.argv) > 2 and sys.argv[1] == "--date":
        target_date = sys.argv[2]

    print(f"=== 推送今日资讯摘要 ({target_date}) ===")

    data = load_today_news(target_date)
    if not data:
        print(f"  ⚠️ 无 {target_date} 的新闻数据，跳过推送")
        return

    news_count = data.get("count", len(data.get("news", [])))
    print(f"  新闻总数: {news_count}")
    if news_count == 0:
        print(f"  ⚠️ 今日新闻为空，跳过推送")
        return

    content = build_digest_md(data)
    if not content:
        print(f"  ⚠️ 构建摘要失败，跳过推送")
        return

    print(f"  摘要长度: {len(content)} 字")
    # 本地保存一份供调试
    try:
        with open(os.path.join(BASE, "today_digest.md"), "w", encoding="utf-8") as f:
            f.write(content)
    except Exception:
        pass

    push_to_pushdeer(content)


if __name__ == "__main__":
    main()
