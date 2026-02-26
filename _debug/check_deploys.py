import json
import os
import urllib.request

token = os.environ["VERCEL_TOKEN"]

for proj, name in [
    ("prj_pM0jSF8SLL6xheNPTqt0TWmAasYU", "marketing"),
    ("prj_7uWhAMwVWvnKte9HfhxkKBNlbMRz", "frontend"),
]:
    req = urllib.request.Request(
        f"https://api.vercel.com/v6/deployments?projectId={proj}&limit=3",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.load(r)
        print(f"\n=== {name} ===")
        for dep in d.get("deployments", [])[:3]:
            print(f"  {dep.get('state')} | {dep.get('url')} | {dep.get('uid')}")
