#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI算力产业链每日资讯 — 生产全自动流水线
流程：采集新闻 → 构建前端 → 部署OSS → 刷新CDN
定时任务：Windows Task Scheduler 每天 08:30 触发（周一至周五）
"""
import os, sys, subprocess, json, time, traceback
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
NEWS_SITE = os.path.join(BASE, "news_site")
LOG_DIR = os.path.join(BASE, "logs", "pipeline")
os.makedirs(LOG_DIR, exist_ok=True)

BEIJING_TZ = timezone(timedelta(hours=8))

def log(msg, type="INFO"):
    ts = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{type}] {msg}"
    print(line)
    fp = os.path.join(LOG_DIR, f"pipeline_{datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')}.log")
    with open(fp, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def run_cmd(cmd, cwd=None):
    log(f"执行: {cmd}")
    r = subprocess.run(cmd, shell=True, cwd=cwd or BASE,
                       capture_output=True, text=True, timeout=600)
    for line in r.stdout.strip().split("\n"):
        if line.strip():
            log(f"  {line}")
    if r.returncode != 0:
        for line in r.stderr.strip().split("\n"):
            if line.strip():
                log(f"  ERROR: {line}", "ERROR")
    return r.returncode == 0


def main():
    log("=" * 50)
    log("AI算力产业链每日资讯 — 生产流水线启动")
    log("=" * 50)

    # 检查是否周末
    today = datetime.now(BEIJING_TZ)
    if today.weekday() >= 5:
        log(f"周末 ({today.strftime('%A')})，跳过执行", "SKIP")
        return

    today_str = today.strftime("%Y-%m-%d")

    # ============ Step 1: 采集新闻 ============
    log(f"\n[1/4] 采集新闻 ({today_str})...")
    pipeline_py = os.path.join(BASE, "daily_pipeline.py")
    if not os.path.exists(pipeline_py):
        log(f"  找不到 {pipeline_py}", "ERROR")
        return
    ok = run_cmd(f"python \"{pipeline_py}\"")
    if not ok:
        log("  新闻采集失败，中止流水线", "ERROR")
        return

    # ============ Step 2: 构建前端 ============
    log(f"\n[2/4] 构建前端...")
    ok = run_cmd("npx vite build", cwd=NEWS_SITE)
    if not ok:
        log("  前端构建失败，中止流水线", "ERROR")
        return

    dist_dir = os.path.join(NEWS_SITE, "dist")
    if not os.path.isdir(dist_dir) or not os.listdir(dist_dir):
        log(f"  dist/ 为空或不存在 ({dist_dir})", "ERROR")
        return

    # ============ Step 3: 验证数据完整性 ============
    log(f"\n[3/4] 验证数据完整性...")
    verify_py = os.path.join(NEWS_SITE, "verify_deploy.py")
    if not os.path.exists(verify_py):
        log(f"  找不到验证脚本 {verify_py}，跳过", "WARN")
    else:
        ok = run_cmd(f"python \"{verify_py}\"")
        if not ok:
            log("  数据完整性验证失败，中止流水线（请检查 daily_pipeline.py 的硬编码补全逻辑）", "ERROR")
            return

    # ============ Step 4: 部署到 OSS + 刷新 CDN ============
    log(f"\n[4/4] 部署到 OSS + 刷新 CDN...")

    deploy_py = os.path.join(NEWS_SITE, "deploy_minimal.py")
    if not os.path.exists(deploy_py):
        log(f"  找不到部署脚本 {deploy_py}", "ERROR")
        return

    ak_id = os.environ.get("OSS_AK_ID", "")
    ak_secret = os.environ.get("OSS_AK_SECRET", "")
    if not ak_id or not ak_secret:
        log("  无有效 OSS 凭证，跳过部署", "ERROR")
        return

    env = os.environ.copy()
    env["OSS_AK_ID"] = ak_id
    env["OSS_AK_SECRET"] = ak_secret
    r = subprocess.run(f"python \"{deploy_py}\"", shell=True, cwd=BASE,
                       capture_output=True, text=True, timeout=300, env=env)
    for line in r.stdout.strip().split("\n"):
        if line.strip():
            log(f"  {line}")
    if r.returncode != 0:
        for line in r.stderr.strip().split("\n"):
            if line.strip():
                log(f"  ERROR: {line}", "ERROR")
        log("  部署失败", "ERROR")
        return

    log("=" * 50)
    log(f"✅ 生产流水线全部完成!")
    log(f"   访问: https://portfolio-analysis.top/news/index.html")
    log("=" * 50)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"流水线异常: {e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
