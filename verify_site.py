"""验证网站数据"""
import json, os

base = r"d:\TRAE SOLO CN\投资指数资讯\news_site"

# Check index.json
with open(os.path.join(base, "data", "index.json"), "r", encoding="utf-8") as f:
    idx = json.load(f)
print("index.json:", json.dumps(idx, ensure_ascii=False))

# Check 2026-06-22.json
with open(os.path.join(base, "data", "2026-06-22.json"), "r", encoding="utf-8") as f:
    d = json.load(f)
print(f"\n2026-06-22.json: {d['count']}条, 更新时间: {d['updated']}")
print("前5条样本:")
for n in d['news'][:5]:
    ml = n['mainline']
    imp = n['impact']
    title = n['title'][:45]
    print(f"  [{ml}] [{imp}] {title}")

# Summary
print(f"\n主线分布:")
ml_stats = {}
for n in d['news']:
    for ml in n['mainline'].split(", "):
        ml_stats[ml] = ml_stats.get(ml, 0) + 1
for k, v in sorted(ml_stats.items()):
    print(f"  {k}: {v}")

print(f"\n影响程度分布:")
imp_stats = {}
for n in d['news']:
    imp = n['impact']
    imp_stats[imp] = imp_stats.get(imp, 0) + 1
for k, v in sorted(imp_stats.items()):
    print(f"  {k}: {v}")

print(f"\n✅ 网站数据验证完成!")
print(f"📁 {os.path.join(base, 'index.html')}")
