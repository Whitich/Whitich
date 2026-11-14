import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def fetch(url, api=False):
    headers = {"User-Agent": "Whitich-profile"}
    if api and os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return response.read().decode("utf-8")


user = json.loads(fetch("https://api.github.com/users/Whitich", True))
repos = []
page = 1
while True:
    batch = json.loads(fetch(f"https://api.github.com/users/Whitich/repos?per_page=100&page={page}", True))
    repos.extend(batch)
    if len(batch) < 100:
        break
    page += 1
own = [repo for repo in repos if not repo["fork"] and not repo["private"]]
metrics = [(len(own), "Açık kaynak depo"), (sum(r["stargazers_count"] for r in own), "Projelerde yıldız"),
           (user["followers"], "Takipçi"), (len({r["language"] for r in own if r["language"]}), "Ana dil / teknoloji")]
stamp = datetime.now(timezone.utc).strftime("%d.%m.%Y")
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="880" height="190" viewBox="0 0 880 190" role="img" aria-label="GitHub public profile statistics">',
       '<rect x="1" y="1" width="878" height="188" rx="18" fill="#0d1117" stroke="#30363d"/>',
       '<text x="28" y="35" fill="#8b949e" font-family="Segoe UI,Arial,sans-serif" font-size="12" letter-spacing="2">GITHUB / HERKESE AÇIK ÇALIŞMALAR</text>']
for index, (value, label) in enumerate(metrics):
    x = 28 + index * 218
    svg.append(f'<text x="{x}" y="95" fill="#58a6ff" font-family="Segoe UI,Arial,sans-serif" font-weight="700" font-size="40">{value}</text>')
    svg.append(f'<text x="{x}" y="125" fill="#c9d1d9" font-family="Segoe UI,Arial,sans-serif" font-size="15">{label}</text>')
svg.append(f'<text x="28" y="166" fill="#8b949e" font-family="Segoe UI,Arial,sans-serif" font-size="11">GitHub API · {stamp} · Özel depolar dahil değildir. Dil sayısı, depoların ana dillerini esas alır.</text></svg>')
(ROOT / "assets/stats.svg").write_text("\n".join(svg), encoding="utf-8")

html = fetch("https://github.com/Whitich")
badges = re.findall(r'<img\b[^>]*\bsrc="([^"]+)"[^>]*\balt="Achievement: ([^"]+)"[^>]*>', html)
unique = dict((name, url.strip()) for url, name in badges)
if not unique:
    raise RuntimeError("No native achievements found; keeping the existing README badges")
markup = '\n'.join(f'  <img src="{url}" width="88" alt="{name}" />' for name, url in unique.items())
readme = ROOT / "README.md"
content = readme.read_text(encoding="utf-8")
content, count = re.subn(r'<!-- ACHIEVEMENTS:START -->.*?<!-- ACHIEVEMENTS:END -->',
                       '<!-- ACHIEVEMENTS:START -->\n' + markup + '\n<!-- ACHIEVEMENTS:END -->', content, flags=re.S)
if count != 1:
    raise RuntimeError("Expected exactly one achievements block")
readme.write_text(content, encoding="utf-8")
print(f"Updated public statistics and {len(unique)} verified achievements")
