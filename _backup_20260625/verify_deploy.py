"""E2E验证脚本：检查构建产物 + 数据完整性"""
import json, os, sys, re

ok, fail = 0, 0
def check(name, cond):
    global ok, fail
    if cond:
        ok += 1
        print(f"  [PASS] {name}")
    else:
        fail += 1
        print(f"  [FAIL] {name}")

BASE = os.path.dirname(os.path.abspath(__file__))

print("=== L1: 静态结构检查 ===")

# index.html (SPA架构, 内容在JS中)
idx_path = os.path.join(BASE, "dist", "index.html")
with open(idx_path, "r", encoding="utf-8") as f:
    html = f.read()
check("DOCTYPE", "<!doctype html>" in html)
check("root挂载点", 'id="root"' in html)
check("CSS引用", ".css" in html)
check("JS引用", ".js" in html)

# JS bundle (SPA内容)
js_dir = os.path.join(BASE, "dist", "assets")
for fname in os.listdir(js_dir):
    if fname.endswith(".js"):
        js_path = os.path.join(js_dir, fname)
        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()
        check("JS包含 Designed & Built by 郑公泽", "Designed & Built by 郑公泽" in js)
        check("JS包含 header-author class", "header-author" in js)
        check("JS包含 子标题: 上游材料颠覆", "上游材料颠覆" in js and "下游应用爆发" in js)
        break

# CSS
css_dir = os.path.join(BASE, "dist", "assets")
for fname in os.listdir(css_dir):
    if fname.endswith(".css"):
        css_path = os.path.join(css_dir, fname)
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
        check("CSS包含 .header-author", ".header-author{" in css.replace(" ", ""))
        check("CSS .header-author font-weight: 400", "font-weight:400" in css.replace(" ", ""))
        break

print(f"\n=== L2: 数据完整性检查 ===")
data_dir = os.path.join(BASE, "public", "data")
for fname in sorted(os.listdir(data_dir)):
    if not fname.endswith(".json") or fname in ("index.json", "breakthrough.json"):
        continue
    fpath = os.path.join(data_dir, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    news_list = data.get("news", [])
    total = len(news_list)
    missing_analysis = sum(1 for n in news_list if "【产业链影响】" not in n.get("summary", ""))
    missing_conclusion = sum(1 for n in news_list if "【大白话结论】" not in n.get("summary", ""))
    check(f"{fname}: {total}条, 缺产业链影响={missing_analysis}, 缺大白话结论={missing_conclusion}",
          missing_analysis == 0 and missing_conclusion == 0)

# 检查硅电容那条
for fname in sorted(os.listdir(data_dir)):
    if not fname.endswith(".json") or fname in ("breakthrough.json", "index.json"):
        continue
    fpath = os.path.join(data_dir, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        continue
    for item in data.get("news", []):
        if "硅电容" in item["title"]:
            s = item.get("summary", "")
            check(f"硅电容有【产业链影响】", "【产业链影响】" in s)
            check(f"硅电容有【大白话结论】", "【大白话结论】" in s)
            break

print(f"\n{'='*40}")
print(f"  结果: {ok} 通过, {fail} 失败")
print(f"{'='*40}")
sys.exit(0 if fail == 0 else 1)
