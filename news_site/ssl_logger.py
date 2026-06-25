import sys
import os
import json
import time
import traceback
from datetime import datetime, timezone, timedelta

LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs', 'ssl')
os.makedirs(LOG_DIR, exist_ok=True)

BEIJING_TZ = timezone(timedelta(hours=8))


def _ts():
    return datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')


def _log_file(prefix):
    date = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')
    return os.path.join(LOG_DIR, f'{prefix}_{date}.log')


def log_event(prefix, event_type, message, details=None):
    record = {
        'ts': _ts(),
        'type': event_type,
        'msg': message,
    }
    if details:
        record['details'] = details
    line = json.dumps(record, ensure_ascii=False)

    fp = _log_file(prefix)
    with open(fp, 'a', encoding='utf-8') as f:
        f.write(line + '\n')

    prefix_map = {'OK': '✅', 'ERROR': '❌', 'WARN': '⚠️', 'INFO': 'ℹ️'}
    emoji = prefix_map.get(event_type, '📝')
    print(f'{emoji} [{_ts()}] {message}')
    if details:
        print(f'   详情: {details}')
    return fp


def log_error(prefix, message, exc_info=None):
    details = traceback.format_exc() if exc_info else None
    return log_event(prefix, 'ERROR', message, details)


def log_ok(prefix, message, details=None):
    return log_event(prefix, 'OK', message, details)


def log_warn(prefix, message, details=None):
    return log_event(prefix, 'WARN', message, details)


def log_info(prefix, message, details=None):
    return log_event(prefix, 'INFO', message, details)


def read_recent_logs(prefix, lines=50):
    today = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')
    fp = os.path.join(LOG_DIR, f'{prefix}_{today}.log')
    if not os.path.exists(fp):
        fp = _log_file(prefix)
    if not os.path.exists(fp):
        return []
    with open(fp, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
    recent = [json.loads(l) for l in all_lines[-lines:]]
    return recent
