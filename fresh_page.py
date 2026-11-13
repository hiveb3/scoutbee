#!/usr/bin/env python3
# Open source (MIT) · AI-generated with Claude (Anthropic), reviewed by a human · https://github.com/hiveb3/scoutbee
# Keeps Wildflower Watch fresh in the browser: no stale cached copies, and an open page reloads itself
# after 30 minutes (never while the visitor is typing a comment or has a post's details open).
# Usage: python3 fresh_page.py SITEDIR   (run after build_site.py)
import sys, os
p = os.path.join(sys.argv[1], "index.html"); s = open(p, encoding="utf-8").read()
META = ('<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">'
        '<meta http-equiv="Pragma" content="no-cache"><meta http-equiv="Expires" content="0">')
JS = """<script>
(() => { const LOADED = Date.now();
  const busy = () => { const a = document.activeElement;
    return (a && (a.tagName === "TEXTAREA" || a.tagName === "INPUT") && a.value) || document.querySelector(".det:not([hidden])"); };
  const check = () => { if (Date.now() - LOADED > 30 * 60 * 1000 && document.visibilityState === "visible" && !busy()) location.reload(); };
  setInterval(check, 60000); document.addEventListener("visibilitychange", check); })();
</script>"""
# a separator line between the curator's own words and the tips / Wildflower Watch banner
s = s.replace('body += "\\n\\n<sub>" + T("tips_head")', 'body += "\\n\\n---\\n\\n<sub>" + T("tips_head")', 1)
s = s.replace('if (box.querySelector(".sig").checked) body += "\\n\\n" + (BADGE',
              'if (box.querySelector(".sig").checked) body += (body.includes("\\n---\\n") ? "\\n\\n" : "\\n\\n---\\n\\n") + (BADGE', 1)
open(p, "w", encoding="utf-8").write(s)
if "fresh_page" not in s:
    s = s.replace("<head>", "<head>" + META, 1).replace("</body>", JS + "<!-- fresh_page -->\n</body>", 1)
    open(p, "w", encoding="utf-8").write(s)
print("fresh_page: OK")
