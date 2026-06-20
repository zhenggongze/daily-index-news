#!/usr/bin/env python3
"""Push today_report.md via PushDeer. Used by TRAE Schedule instead of Node.js."""
import sys, json, requests, os

with open('today_report.md', 'r', encoding='utf-8') as f:
    content = f.read()

first_line = 'Trae每日指数投资资讯'
key = os.environ.get("PUSHDEER_KEY", "")

for attempt in range(1, 4):
    try:
        r = requests.post('https://api2.pushdeer.com/message/push',
            data={'pushkey': key, 'text': first_line, 'type': 'markdown', 'desp': content},
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
