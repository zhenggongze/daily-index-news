"""查找 DSpark 文章在新版数据中的分类"""
import json, urllib.request

d = json.loads(urllib.request.urlopen(
    "https://portfolio-analysis.top/news/data/2026-06-29.json?_t=v5", timeout=15
).read())

found = False
for n in d["news"]:
    if "DSpark" in n["title"] or "DeepSeeK" in n["title"]:
        found = True
        print(f"标题: {n['title']}")
        print(f"影响: {n['impact']}")
        print(f"主线: {n['mainline']}")
        summary = n.get("summary", "")
        idx = summary.find("影响程度")
        print(f"推理段(前200字): {summary[idx:idx+200]}")
        break

if not found:
    print("DSpark/DeepSeeK 文章不在本轮RSS采集中（RSS随时间变化）")

print(f"\n全量分布:")
imp = {}
for n in d["news"]:
    imp[n["impact"]] = imp.get(n["impact"], 0) + 1
for k in sorted(imp.keys()):
    print(f"  {k}: {imp[k]} 条")
print(f"  总计: {sum(imp.values())} 条")
