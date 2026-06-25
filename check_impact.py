"""检查种子数据的impact检测"""
import json

with open(r'd:\TRAE SOLO CN\投资指数资讯\news_site\public\data\2026-06-22.json', 'r') as f:
    d = json.load(f)

for n in d['news'][:5]:
    has_big = '【影响程度】大' in n['summary']
    has_mid = '【影响程度】中' in n['summary']
    print(f"impact={n['impact']} has_big={has_big} has_mid={has_mid} title={n['title'][:30]}")
    print(f"  start: {n['summary'][:60]}")

# Count actual
big = sum(1 for n in d['news'] if '【影响程度】大' in n['summary'])
mid = sum(1 for n in d['news'] if '【影响程度】中' in n['summary'])
small = sum(1 for n in d['news'] if '【影响程度】小' in n['summary'])
print(f"\n实际分布: 大={big} 中={mid} 小={small} 总计={len(d['news'])}")
print(f"分配中: 大={sum(1 for n in d['news'] if n['impact']=='大')} 中={sum(1 for n in d['news'] if n['impact']=='中')}")
