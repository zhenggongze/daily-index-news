#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全自动 SSL 证书申请 + CDN 部署
使用 ACME (Let's Encrypt) HTTP-01 验证 (通过 OSS 上传验证文件)
"""

import sys
import os
import time
import json

import oss2

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption

import josepy as jose
from acme import client, messages, challenges

from aliyunsdkcore.client import AcsClient
from aliyunsdkcdn.request.v20180510 import SetCdnDomainSSLCertificateRequest

import ssl_logger as log

LETSENCRYPT_DIRECTORY = 'https://acme-v02.api.letsencrypt.org/directory'
DOMAIN = 'portfolio-analysis.top'
CDN_DOMAIN = 'portfolio-analysis.top'
BUCKET_NAME = 'portfolio-analysis-hosting'
REGION = 'cn-hangzhou'
OSS_ENDPOINT = f'oss-{REGION}.aliyuncs.com'

ACC_KEY_FILE = os.path.join(os.path.dirname(__file__), 'ssl_account_key.json')
CERT_DIR = os.path.join(os.path.dirname(__file__), 'ssl_certs')

CHALLENGE_PREFIX = '.well-known/acme-challenge/'


def load_deploy_credentials():
    deploy_path = r'd:\TRAE SOLO CN\各类测试\portfolio-analysis\deploy_v2.py'
    ak_id = None
    ak_secret = None
    with open(deploy_path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('//'):
                continue
            if 'ACCESS_KEY_ID' in stripped and '=' in stripped and not ak_id:
                parts = stripped.split('=')
                val = parts[1].strip().strip("'\"").rstrip("'\"")
                if val and val.startswith('LTAI'):
                    ak_id = val
            if 'ACCESS_KEY_SECRET' in stripped and '=' in stripped and not ak_secret:
                parts = stripped.split('=')
                val = parts[1].strip().strip("'\"").rstrip("'\"")
                if val and len(val) == 30:
                    ak_secret = val
    if not ak_id or not ak_secret:
        msg = f'无法从 {deploy_path} 读取凭证'
        log.log_error('auto_ssl', msg)
        log.log_error('auto_ssl', f'ak_id={"已读取" if ak_id else "未读取"}, ak_secret={"已读取" if ak_secret else "未读取"}')
        sys.exit(1)
    return ak_id, ak_secret


def get_bucket():
    ak_id, ak_secret = load_deploy_credentials()
    auth = oss2.Auth(ak_id, ak_secret)
    return oss2.Bucket(auth, OSS_ENDPOINT, BUCKET_NAME)


def get_cdn_client():
    ak_id, ak_secret = load_deploy_credentials()
    return AcsClient(ak_id, ak_secret, REGION)


def upload_http_challenge(bucket, token, key_auth):
    key = CHALLENGE_PREFIX + token
    print(f"  上传验证文件到 OSS: {key}")
    bucket.put_object(
        key, key_auth.encode('utf-8'),
        headers={
            'Content-Type': 'text/plain',
            'Cache-Control': 'no-cache',
        }
    )
    url = f'http://{DOMAIN}/{key}'
    print(f"  验证 URL: {url}")
    return key


def delete_http_challenge(bucket, keys):
    for key in keys:
        try:
            bucket.delete_object(key)
            print(f"  已删除: {key}")
        except Exception as e:
            print(f"  删除失败 {key}: {e}")


def upload_cert_to_cdn(client, cert_pem, key_pem):
    print(f"  上传证书到 CDN: {CDN_DOMAIN}")
    req = SetCdnDomainSSLCertificateRequest.SetCdnDomainSSLCertificateRequest()
    req.set_DomainName(CDN_DOMAIN)
    req.set_SSLPub(cert_pem)
    req.set_SSLPri(key_pem)
    req.set_CertType('upload')
    req.set_SSLProtocol('on')
    resp = client.do_action_with_exception(req)
    print(f"  CDN 证书已更新: {resp}")


def generate_csr(domain):
    print(f"  生成域名密钥和 CSR: {domain}")
    key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    csr = x509.CertificateSigningRequestBuilder().subject_name(
        x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, domain)])
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(domain)]),
        critical=False,
    ).sign(key, hashes.SHA256(), default_backend())

    key_pem = key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption(),
    ).decode('utf-8')

    csr_pem = csr.public_bytes(Encoding.PEM)

    print(f"  CSR 已生成")
    return csr_pem, key_pem


def main():
    LOG_PREFIX = 'auto_ssl'

    log.log_info(LOG_PREFIX, '=' * 50)
    log.log_info(LOG_PREFIX, '开始 SSL 证书自动申请')
    log.log_info(LOG_PREFIX, f'域名: {DOMAIN}')
    log.log_info(LOG_PREFIX, '=' * 50)

    os.makedirs(CERT_DIR, exist_ok=True)

    bucket = get_bucket()
    cdn_client = get_cdn_client()
    log.log_ok(LOG_PREFIX, '阿里云凭证已加载 (OSS + CDN)')

    log.log_info(LOG_PREFIX, '连接 Let\'s Encrypt...')
    net = client.ClientNetwork(key=None, account=None)
    directory = messages.Directory.from_json(
        net.get(LETSENCRYPT_DIRECTORY).json()
    )
    log.log_ok(LOG_PREFIX, 'Let\'s Encrypt 目录已获取')

    log.log_info(LOG_PREFIX, '创建 ACME 账户...')
    acc_key = jose.JWKRSA(key=rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    ))
    with open(ACC_KEY_FILE, 'w') as f:
        json.dump({'key': acc_key.json_dumps()}, f)

    net = client.ClientNetwork(key=acc_key)
    acme_client = client.ClientV2(directory, net=net)

    regr = acme_client.new_account(
        messages.NewRegistration.from_data(
            email='admin@portfolio-analysis.top',
            terms_of_service_agreed=True,
        )
    )
    log.log_ok(LOG_PREFIX, f'ACME 账户已创建: {regr.uri}')

    log.log_info(LOG_PREFIX, '生成域名证书 CSR...')
    csr_obj, domain_key_pem = generate_csr(DOMAIN)
    log.log_ok(LOG_PREFIX, '密钥和 CSR 已生成')

    log.log_info(LOG_PREFIX, '请求证书并完成 HTTP-01 验证...')
    orderr = acme_client.new_order(csr_obj)

    authz_list = orderr.authorizations
    log.log_info(LOG_PREFIX, f'授权数量: {len(authz_list)}')

    challenge_keys = []

    for authz in authz_list:
        authz_body = authz.body
        log.log_info(LOG_PREFIX, f'授权域名: {authz_body.identifier.value}')

        http_challenge = None
        for ch in authz_body.challenges:
            if isinstance(ch.chall, challenges.HTTP01):
                http_challenge = ch
                break

        if not http_challenge:
            log.log_error(LOG_PREFIX, '未找到 HTTP-01 验证方式')
            sys.exit(1)

        chall_response = http_challenge.chall.response(acc_key)
        key_auth = chall_response.key_authorization
        token = http_challenge.chall.encode('token')

        log.log_info(LOG_PREFIX, f'Token: {token}')

        oss_key = upload_http_challenge(bucket, token, key_auth)
        challenge_keys.append(oss_key)

        log.log_info(LOG_PREFIX, '等待 OSS/CDN 可访问 (15秒)...')
        time.sleep(15)

        log.log_info(LOG_PREFIX, '提交验证...')
        try:
            acme_client.answer_challenge(http_challenge, chall_response)
            log.log_ok(LOG_PREFIX, '验证已提交')
        except Exception as e:
            log.log_error(LOG_PREFIX, f'提交验证出错: {e}')
            log.log_error(LOG_PREFIX, f'错误详情', exc_info=True)

    log.log_info(LOG_PREFIX, '等待 Let\'s Encrypt 验证 (10秒)...')
    time.sleep(10)

    log.log_info(LOG_PREFIX, '获取证书...')
    try:
        final_order = acme_client.poll_and_finalize(orderr)
        cert_fullchain = final_order.fullchain_pem
        log.log_ok(LOG_PREFIX, f'证书已获取 ({len(cert_fullchain)} 字符)')
    except Exception as e:
        log.log_error(LOG_PREFIX, f'获取证书失败: {e}')
        log.log_error(LOG_PREFIX, '错误详情', exc_info=True)
        delete_http_challenge(bucket, challenge_keys)
        sys.exit(1)

    cert_path = os.path.join(CERT_DIR, 'fullchain.pem')
    key_path = os.path.join(CERT_DIR, 'privkey.pem')

    with open(cert_path, 'w') as f:
        f.write(cert_fullchain)
    with open(key_path, 'w') as f:
        f.write(domain_key_pem)

    log.log_ok(LOG_PREFIX, f'证书已保存: {cert_path}')
    log.log_ok(LOG_PREFIX, f'密钥已保存: {key_path}')

    log.log_info(LOG_PREFIX, '上传证书到阿里云 CDN...')
    upload_cert_to_cdn(cdn_client, cert_fullchain, domain_key_pem)
    log.log_ok(LOG_PREFIX, 'CDN 证书已更新')

    log.log_info(LOG_PREFIX, '清理 OSS 验证文件...')
    delete_http_challenge(bucket, challenge_keys)

    log.log_ok(LOG_PREFIX, 'SSL 证书申请 + CDN 部署完成')
    log.log_ok(LOG_PREFIX, f'访问: https://{DOMAIN}/news/index.html')
    log.log_warn(LOG_PREFIX, '证书有效期: 90天，到期后需重新申请')


if __name__ == '__main__':
    main()
