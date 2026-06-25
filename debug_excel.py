"""调试Excel生成问题"""
import sys, os
BASE = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(BASE, ".trae", "skills", "a-stock-data")
sys.path.insert(0, SKILLS_DIR)

from fetch_ai_news import create_excel, match_mainline, FETCH_DAYS
from datetime import datetime, timedelta
import random

test_primary = [
    {'source': '华尔街见闻', 'title': '英伟达GB200量产推动供应链升级', 'summary': '英伟达GB200已进入量产阶段', 'link': 'https://example.com/1', 'pub_date': datetime.now()},
    {'source': 'IT之家', 'title': '华为昇腾910C通过阿里云大规模验证', 'summary': '华为昇腾910C芯片已在阿里云完成大规模部署验证', 'link': 'https://example.com/2', 'pub_date': datetime.now()},
]

primary = []
for i in range(100):
    t = random.choice(test_primary)
    primary.append({
        'source': t['source'],
        'title': f'{t["title"]} - #{i+1}',
        'summary': t['summary'],
        'link': t['link'] + f'?id={i}',
        'pub_date': datetime.now() - timedelta(hours=random.randint(0, 720))
    })

secondary = random.sample(primary, min(50, len(primary)))

path = create_excel(primary, secondary)

with open(path, 'rb') as f:
    head = f.read(4)
    print(f'File: {path}')
    print(f'Size: {os.path.getsize(path)}')
    print(f'Header hex: {head.hex()}')
    print(f'Starts with PK: {head == b"PK\x03\x04"}')
