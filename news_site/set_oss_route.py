"""设置OSS路由规则：/news/ → /news/index.html"""
import requests, os, base64, hmac, hashlib, time

AK = os.environ.get("OSS_AK_ID", "")
SK = os.environ.get("OSS_AK_SECRET", "")
if not AK or not SK:
    print("❌ 请设置 OSS_AK_ID / OSS_AK_SECRET 环境变量")
    exit(1)
BUCKET = "portfolio-analysis-hosting"
REGION = "oss-cn-hangzhou"
HOST = f"{BUCKET}.{REGION}.aliyuncs.com"

XML_BODY = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    "<WebsiteConfiguration>"
    "  <IndexDocument><Suffix>index.html</Suffix></IndexDocument>"
    "  <ErrorDocument><Key>error.html</Key></ErrorDocument>"
    "  <RoutingRules>"
    "    <RoutingRule>"
    "      <RuleNumber>1</RuleNumber>"
    "      <Condition>"
    "        <KeyPrefixEquals>news/</KeyPrefixEquals>"
    "        <HttpErrorCodeReturnedEquals>404</HttpErrorCodeReturnedEquals>"
    "      </Condition>"
    "      <Redirect>"
    "        <Protocol>https</Protocol>"
    "        <HostName>portfolio-analysis.top</HostName>"
    "        <ReplaceKeyPrefixWith>news/index.html</ReplaceKeyPrefixWith>"
    "        <HttpRedirectCode>302</HttpRedirectCode>"
    "      </Redirect>"
    "    </RoutingRule>"
    "  </RoutingRules>"
    "</WebsiteConfiguration>"
)

ts = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
ct = "application/xml"
resource = "/?website"
sts = f"PUT\n\n{ct}\n{ts}\n{resource}"
sig = base64.b64encode(hmac.new(SK.encode(), sts.encode(), hashlib.sha1).digest()).decode()

r = requests.put(
    f"https://{HOST}/?website",
    data=XML_BODY.encode(),
    headers={"Content-Type": ct, "Date": ts, "Authorization": f"OSS {AK}:{sig}"},
)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print("OSS routing rule set OK")
else:
    print(r.text[:500])
