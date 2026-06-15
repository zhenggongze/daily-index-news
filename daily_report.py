#!/usr/bin/env python3
"""GitHub Actions每日推送 — 读取today_report.md并通过PushDeer推送"""
import os, sys, requests, datetime

REPORT_PATH = 'today_report.md'
PUSHDEER_KEY = os.environ.get('PUSHDEER_KEY', 'PDU41552TCTtotgq3EC5AvTOaXpiZG0eMTR6VAl8v')
PUSHDEER_URL = 'https://api2.pushdeer.com/message/push'

today = datetime.date.today().strftime('%Y-%m-%d')

if not os.path.exists(REPORT_PATH):
    print(f'NO_REPORT: {REPORT_PATH} not found, skipping')
    sys.exit(0)

with open(REPORT_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

if len(content) < 500:
    print(f'REPORT_TOO_SHORT: {len(content)} chars, skipping')
    sys.exit(0)

text = 'Trae每日指数投资资讯'

for attempt in range(1, 4):
    try:
        r = requests.post(PUSHDEER_URL,
            data={'pushkey': PUSHDEER_KEY, 'text': text, 'type': 'markdown', 'desp': content},
            timeout=30)
        j = r.json()
        if j.get('code') == 0:
            print('PUSH_SUCCESS')
            sys.exit(0)
        else:
            print(f'PUSH_FAILED:{j.get("error","unknown")}')
    except Exception as e:
        print(f'REQUEST_ERROR:{e}')
    if attempt < 3:
        import time
        time.sleep(3)

print('PUSH_FAILED:max_retries_exceeded')
sys.exit(1)
