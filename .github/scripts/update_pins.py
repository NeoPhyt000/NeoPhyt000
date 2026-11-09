import os
import re
import sys
import json
import urllib.request
import urllib.error

user = os.environ["GH_USER"]
token = os.environ["GH_TOKEN"]

query = """
query($login: String!) {
  user(login: $login) {
    pinnedItems(first: 6, types: REPOSITORY) {
      nodes { ... on Repository { name } }
    }
  }
}
"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": query, "variables": {"login": user}}).encode(),
    headers={
        "Authorization": "bearer " + token,
        "Content-Type": "application/json",
        "User-Agent": "pins-updater",
    },
)

try:
    data = json.load(urllib.request.urlopen(req))
except urllib.error.HTTPError as e:
    print("HTTP error:", e.code, e.read().decode())
    sys.exit(1)

if "errors" in data:
    print("GraphQL error:", json.dumps(data["errors"], indent=2))
    sys.exit(1)

names = [n["name"] for n in data["data"]["user"]["pinnedItems"]["nodes"] if n]

if not names:
    print("No pinned repos found, leaving README unchanged.")
    sys.exit(0)


def card(n):
    return (
        '<td width="50%" align="center">'
        f'<a href="https://github.com/{user}/{n}">'
        f'<img src="https://github-readme-stats.shion.dev/api/pin/?username={user}&repo={n}&theme=prussian&hide_border=false" alt="{n}" />'
        "</a></td>"
    )


rows = []
for i in range(0, len(names), 2):
    pair = names[i:i + 2]
    cells = "\n    ".join(card(n) for n in pair)
    if len(pair) == 1:
        cells += '\n    <td width="50%"></td>'
    rows.append(f"  <tr>\n    {cells}\n  </tr>")

block = "<table>\n" + "\n".join(rows) + "\n</table>"

text = open("README.md", encoding="utf-8").read()
pattern = re.compile(r"(<!-- PINNED:START -->).*?(<!-- PINNED:END -->)", re.DOTALL)

if not pattern.search(text):
    print("ERROR: PINNED:START / PINNED:END markers not found in README.md")
    sys.exit(1)

new = pattern.sub(lambda m: m.group(1) + "\n" + block + "\n" + m.group(2), text)
open("README.md", "w", encoding="utf-8").write(new)
print("Pinned repos:", names)
