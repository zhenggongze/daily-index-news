#!/usr/bin/env python3
"""
幂等检查：检查 OSS 上今天的新闻数据是否已生成。
- 有数据（news_count>0）→ exit 0 → workflow 跳过流水线，直接结束
- 无数据 → exit 1 → workflow 继续执行流水线
- 异常 → exit 1 → fail open，继续执行（宁可重复跑也不能漏掉）

用法：
  python check_oss_today.py
  FORCE_REFRESH=1 python check_oss_today.py  # 强制重新生成，exit 1
"""
import os
import sys
import json
from datetime import date

# 强制刷新模式：直接跳过幂等检查
if os.environ.get("FORCE_REFRESH", "") == "1":
    print("FORCE_REFRESH=1，跳过幂等检查，执行流水线")
    sys.exit(1)

OSS_AK_ID = os.environ.get("OSS_AK_ID", "")
OSS_AK_SECRET = os.environ.get("OSS_AK_SECRET", "")

if not OSS_AK_ID or not OSS_AK_SECRET:
    print("未配置 OSS 凭据，fail open 执行流水线")
    sys.exit(1)

import oss2

BUCKET = "portfolio-analysis-hosting"
ENDPOINT = "https://oss-cn-hangzhou.aliyuncs.com"
today_str = date.today().strftime("%Y-%m-%d")
oss_key = f"news/data/{today_str}.json"

try:
    auth = oss2.Auth(OSS_AK_ID, OSS_AK_SECRET)
    bucket = oss2.Bucket(auth, ENDPOINT, BUCKET, connect_timeout=10)
    obj = bucket.get_object(oss_key)
    data = json.loads(obj.read())
    news_count = data.get("count", len(data.get("news", [])))
    if news_count > 0:
        print(f"TODAY_DATA_EXISTS: {today_str} 已有 {news_count} 条新闻，跳过流水线")
        sys.exit(0)
    else:
        print(f"TODAY_DATA_EMPTY: {today_str} 新闻数为0，执行流水线")
        sys.exit(1)
except oss2.exceptions.NoSuchKey:
    print(f"TODAY_DATA_NOT_FOUND: {today_str} 无数据文件，执行流水线")
    sys.exit(1)
except oss2.exceptions.ServerError as e:
    print(f"OSS_SERVER_ERROR: {e}，fail open 执行流水线")
    sys.exit(1)
except Exception as e:
    print(f"CHECK_FAILED: {e}，fail open 执行流水线")
    sys.exit(1)
