"""修复OSS静态网站配置：/news/ 正确指向 /news/index.html"""
import oss2, os
from oss2.models import BucketWebsite, RoutingRule, Condition, Redirect

AK = os.environ.get("OSS_AK_ID", "")
SK = os.environ.get("OSS_AK_SECRET", "")
if not AK or not SK:
    print("❌ 请设置 OSS_AK_ID / OSS_AK_SECRET 环境变量")
    exit(1)
auth = oss2.Auth(AK, SK)
bucket = oss2.Bucket(auth, "https://oss-cn-hangzhou.aliyuncs.com", "portfolio-analysis-hosting")

bucket.put_object("error.html", b"<html><body>not found</body></html>")
print("Uploaded error.html")

rule = RoutingRule(
    rule_num=1,
    condition=Condition(key_prefix_equals="news/", http_err_code_return_equals="404"),
    redirect=Redirect(
        redirect_type="AliCDN", proto="https",
        host_name="portfolio-analysis.top",
        replace_key_prefix_with="/news/index.html",
        http_redirect_code=302
    )
)
bucket.put_bucket_website(BucketWebsite("index.html", "error.html", [rule]))
print("OK")
