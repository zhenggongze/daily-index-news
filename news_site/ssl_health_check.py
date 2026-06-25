import sys
import os
import socket
import ssl as ssl_mod
import urllib.request
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(__file__))
import ssl_logger as log

DOMAIN = 'portfolio-analysis.top'
URLS = [
    f'https://{DOMAIN}/news/index.html',
    f'https://{DOMAIN}/news/data/index.json',
]
LOG_PREFIX = 'health'


def check_certificate():
    ctx = ssl_mod.create_default_context()
    with socket.create_connection((DOMAIN, 443), timeout=10) as sock:
        with ctx.wrap_socket(sock, server_hostname=DOMAIN) as ssock:
            cert = ssock.getpeercert()

    not_before_str = cert.get('notBefore')
    not_after_str = cert.get('notAfter')

    not_before = datetime.strptime(not_before_str, '%b %d %H:%M:%S %Y %Z').replace(tzinfo=timezone.utc)
    not_after = datetime.strptime(not_after_str, '%b %d %H:%M:%S %Y %Z').replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    days_left = (not_after - now).days

    subject = dict(x[0] for x in cert.get('subject', []))
    issuer = dict(x[0] for x in cert.get('issuer', []))

    beijing = timezone(timedelta(hours=8))
    expire_beijing = not_after.astimezone(beijing).strftime('%Y-%m-%d %H:%M')

    if days_left < 0:
        log.log_error(LOG_PREFIX, f'证书已过期! 过期于 {expire_beijing}')
        return False
    elif days_left < 7:
        log.log_warn(LOG_PREFIX, f'证书即将过期, 剩余 {days_left} 天 (过期: {expire_beijing})')
    elif days_left < 30:
        log.log_info(LOG_PREFIX, f'证书剩余 {days_left} 天 (过期: {expire_beijing}), 建议近期续期')
    else:
        log.log_ok(LOG_PREFIX, f'证书有效, 剩余 {days_left} 天 (过期: {expire_beijing})')

    log.log_info(LOG_PREFIX, f'颁发者: {issuer.get("organizationName", "?")} ({issuer.get("commonName", "?")})')
    log.log_info(LOG_PREFIX, f'域名: {subject.get("commonName", "?")}')
    return True


def check_url(url):
    ctx = ssl_mod.create_default_context()
    req = urllib.request.Request(url)
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=15)
        ct = resp.headers.get('Content-Type', '?')
        body_len = len(resp.read())
        log.log_ok(LOG_PREFIX, f'{url} -> {resp.status} ({ct}, {body_len} bytes)')
        return True
    except urllib.error.HTTPError as e:
        log.log_error(LOG_PREFIX, f'{url} -> HTTP {e.code}: {e.reason}')
        return False
    except urllib.error.URLError as e:
        log.log_error(LOG_PREFIX, f'{url} -> 连接失败: {e.reason}')
        return False
    except Exception as e:
        log.log_error(LOG_PREFIX, f'{url} -> 异常: {e}')
        log.log_error(LOG_PREFIX, '错误详情', exc_info=True)
        return False


def check_dns():
    try:
        ip = socket.getaddrinfo(DOMAIN, 443)[0][4][0]
        log.log_ok(LOG_PREFIX, f'DNS 解析: {DOMAIN} -> {ip}')
        return True
    except Exception as e:
        log.log_error(LOG_PREFIX, f'DNS 解析失败: {e}')
        return False


def main():
    log.log_info(LOG_PREFIX, '=' * 40)
    log.log_info(LOG_PREFIX, 'SSL 健康检查开始')
    log.log_info(LOG_PREFIX, '=' * 40)

    results = []

    log.log_info(LOG_PREFIX, '--- DNS 检查 ---')
    results.append(('DNS 解析', check_dns()))

    log.log_info(LOG_PREFIX, '--- 证书检查 ---')
    results.append(('SSL 证书', check_certificate()))

    log.log_info(LOG_PREFIX, '--- 页面检查 ---')
    url_results = []
    for url in URLS:
        url_results.append(check_url(url))
    all_urls_ok = all(url_results)
    results.append(('页面加载', all_urls_ok))

    log.log_info(LOG_PREFIX, '=' * 40)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    if passed == total:
        log.log_ok(LOG_PREFIX, f'健康检查: {passed}/{total} 通过 ✅')
        return 0
    else:
        failed = [name for name, ok in results if not ok]
        log.log_error(LOG_PREFIX, f'健康检查: {passed}/{total} 通过 ❌ 失败项: {failed}')
        log.log_info(LOG_PREFIX, '如需重新申请证书, 运行: python auto_ssl.py')
        return 1


if __name__ == '__main__':
    sys.exit(main())
