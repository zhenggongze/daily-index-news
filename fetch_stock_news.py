"""
从a-stock-data获取AI算力产业链关键公司个股新闻，补充到现有Excel中
"""
import sys, os, json, re, time
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(BASE, ".trae", "skills", "a-stock-data")
sys.path.insert(0, SKILLS_DIR)
from scripts.news import stock_news

# AI算力产业链关键公司
STOCKS = [
    ("688981", "中芯国际", "A"),
    ("002371", "北方华创", "A"),
    ("688012", "中微公司", "A"),
    ("688256", "寒武纪", "A"),
    ("688041", "海光信息", "A"),
    ("603986", "兆易创新", "A"),
    ("002156", "通富微电", "A"),
    ("300308", "中际旭创", "B"),
    ("300394", "天孚通信", "B"),
    ("300502", "新易盛", "B"),
    ("002475", "立讯精密", "B"),
    ("601138", "工业富联", "B"),
    ("002463", "沪电股份", "B"),
    ("300476", "胜宏科技", "B"),
    ("688017", "绿的谐波", "C"),
    ("002472", "双环传动", "C"),
    ("300124", "汇川技术", "C"),
    ("002050", "三花智控", "C"),
    ("603728", "鸣志电器", "C"),
]

def clean_html(text):
    return re.sub(r'<[^>]+>', '', text).strip()

results = []
for code, name, ml in STOCKS:
    print(f"[{ml}] {name}({code})...")
    try:
        news = stock_news(code, max_pages=2)
        if news:
            for item in news:
                title = item.get("title", "").strip()
                date_str = item.get("date", item.get("showDate", ""))
                summary = clean_html(item.get("summary", item.get("content", "")))[:300]
                if not title:
                    continue
                results.append({
                    "source": f"东方财富-{name}",
                    "title": title,
                    "summary": summary,
                    "pub_date": date_str[:10] if date_str else "",
                    "mainline": ml,
                    "company": name
                })
            print(f"  ✅ {len(news)} 条")
        else:
            print(f"  ⚠️ 无新闻")
    except Exception as e:
        print(f"  ❌ {e}")
    time.sleep(0.5)

# 保存为JSON
output = json.dumps(results, ensure_ascii=False, indent=2)
with open(os.path.join(BASE, "stock_news_extra.json"), "w", encoding="utf-8") as f:
    f.write(output)

print(f"\n✅ 共获取 {len(results)} 条个股新闻")
print(f"主线分布: A={sum(1 for r in results if r['mainline']=='A')}, "
      f"B={sum(1 for r in results if r['mainline']=='B')}, "
      f"C={sum(1 for r in results if r['mainline']=='C')}")
