"""Adds or replaces keys in Tela/ui/i18n.js. Usage: python addkeys.py keys.json"""
import json, re, sys
p = "/home/claude/Tela/ui/i18n.js"
s = open(p, encoding="utf-8").read()
data = json.load(open(sys.argv[1], encoding="utf-8"))
langs = ["pt", "en", "es", "zh"]
for lang in langs:
    start = s.index(f"\n  {lang}: {{\n")
    end = s.index("\n  },", start)
    block = s[start:end]
    adds = []
    for k, v in data.get(lang, {}).items():
        lit = json.dumps(v, ensure_ascii=False)
        pat = re.compile(r'("' + re.escape(k) + r'":\s*)"(?:[^"\\]|\\.)*"')
        if pat.search(block):
            block = pat.sub(lambda m: m.group(1) + lit, block, count=1)
        else:
            adds.append(f'    "{k}": {lit},')
    if adds:
        if not block.rstrip().endswith(","):
            block = block.rstrip() + ","
        block = block + "\n" + "\n".join(adds)
    s = s[:start] + block + s[end:]
open(p, "w", encoding="utf-8").write(s)
missing = [k for k in data.get("pt", {}) if any(k not in data.get(l, {}) for l in langs)]
print("ok", {l: len(data.get(l, {})) for l in langs}, "missing in some:", missing)
