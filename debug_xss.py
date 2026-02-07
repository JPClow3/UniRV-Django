import os, django

os.environ["DJANGO_SETTINGS_MODULE"] = "UniRV_Django.settings"
django.setup()
from django.test import Client
from django.contrib.auth.models import User
from editais.models import Startup
from django.test.utils import setup_test_environment

setup_test_environment()

from django.test.runner import DiscoverRunner

runner = DiscoverRunner()
old_config = runner.setup_databases()

u = User.objects.create_user("testx", "t@t.com", "pass123")
s = Startup.objects.create(
    name="XSS Test",
    description='<script>alert("XSS")</script>',
    category="other",
    status="pre_incubacao",
    proponente=u,
)
print("Stored desc:", repr(s.description))
c = Client()
r = c.get("/startups/")
content = r.content.decode()
print("XSS Test in content:", "XSS Test" in content)
print("escaped script in content:", "&lt;script&gt;" in content)
print("raw script in content:", "<script>alert" in content)
# Find all occurrences of XSS Test
start = 0
occ = 0
while True:
    idx = content.find("XSS Test", start)
    if idx < 0:
        break
    occ += 1
    print(f"OCCURRENCE {occ} at {idx}:", repr(content[max(0, idx - 50) : idx + 300]))
    start = idx + 1

# Search for "leading-relaxed" which is the class around description
desc_idx = content.find("leading-relaxed")
if desc_idx > 0:
    print("DESC_AREA:", repr(content[desc_idx : desc_idx + 400]))

# Check for alert
print("alert_in_content:", "alert" in content)
print("lt_script_in_content:", "&lt;script" in content)
runner.teardown_databases(old_config)
