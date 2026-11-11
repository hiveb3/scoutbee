#!/usr/bin/env python3
# Open source (MIT) · AI-generated with Claude (Anthropic), reviewed by a human · https://github.com/hiveb3/scoutbee
# Scout Bee - builds the Wildflower Watch web page from scout.py output.
# Usage: python3 build_site.py OUTDIR SITEDIR   (OUTDIR has candidates.json + stats.json)  -> SITEDIR/index.html, SITEDIR/data.json
import sys, os, json, html, datetime as dt

OUT, SITE = sys.argv[1], sys.argv[2]
os.makedirs(SITE, exist_ok=True)
posts = json.load(open(os.path.join(OUT, "candidates.json")))
stats = json.load(open(os.path.join(OUT, "stats.json")))
gen = stats.get("generated") or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
skipped = sum(stats.get("why", {}).values())

data = [dict(t=p.get("t") or "(untitled)", a=p["a"], p=p["p"], c=p.get("cat", ""), ct=p.get("ctitle") or p.get("cat", ""),
             w=p.get("nw", 0), i=p.get("imgs", 0), cr=p["created"] + "Z", pend=round(p.get("pending", 0), 2),
             v=p.get("votes", 0), o=p.get("orig", "unchecked")) for p in posts]
json.dump(dict(generated=gen, posts=data, window=stats.get("window"), skipped=skipped, median=stats.get("median")),
          open(os.path.join(SITE, "data.json"), "w"), ensure_ascii=False)

page = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Wildflower Watch</title>
<meta name="description" content="Fresh, well-made Hive posts still waiting for their first visit. Updated every hour by Scout Bee.">
<style>
:root{--bg:#fff8e7;--card:#ffffff;--fg:#3b2a1a;--muted:#7a6448;--line:#ecd9a8;--honey:#e09a00;--honey-soft:#fff0c2;--ok:#2e7d46;--warn:#9a6a00}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#1c1912;--card:#262118;--fg:#f3e9d2;--muted:#b9a582;--line:#43392a;--honey:#f2b705;--honey-soft:#3a3020;--ok:#6fcf8f;--warn:#e8b84a}}
:root[data-theme="dark"]{--bg:#1c1912;--card:#262118;--fg:#f3e9d2;--muted:#b9a582;--line:#43392a;--honey:#f2b705;--honey-soft:#3a3020;--ok:#6fcf8f;--warn:#e8b84a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
.wrap{max-width:860px;margin:0 auto;padding:16px}
h1{font-size:28px;margin:8px 0 4px}.sub{color:var(--muted);margin:0 0 14px}
.upd{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;background:var(--honey-soft);border:2px solid var(--honey);border-radius:12px;padding:12px 14px;margin:0 0 16px}
.upd b{font-size:17px}.upd .ago{font-weight:700;color:var(--honey)}.upd .stale{color:#c62828}
.bar{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px}
.bar input,.bar select{flex:1 1 180px;min-width:0;padding:9px 10px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--fg);font:inherit}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:0 0 10px}
.card h2{font-size:17px;margin:0 0 4px;line-height:1.35}.card h2 a{color:var(--fg);text-decoration:none}.card h2 a:hover{text-decoration:underline}
.meta{color:var(--muted);font-size:14px}.meta a{color:var(--muted)}
.row{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;align-items:center}
.btn{display:inline-block;padding:5px 10px;border-radius:8px;border:1px solid var(--honey);color:var(--fg);text-decoration:none;font-size:14px}
.btn:hover{background:var(--honey-soft)}
.badge{font-size:12px;padding:2px 8px;border-radius:99px;border:1px solid var(--line)}.badge.ok{color:var(--ok);border-color:var(--ok)}.badge.un{color:var(--warn)}
.empty{color:var(--muted);text-align:center;padding:30px 0}
footer{color:var(--muted);font-size:14px;border-top:1px solid var(--line);margin-top:22px;padding-top:12px}
footer a{color:var(--honey)}footer li{margin:2px 0}
</style></head><body><div class="wrap">
<h1>🌼 Wildflower Watch</h1>
<p class="sub">Fresh, well-made Hive posts that are <b>still waiting for their first visit</b>, least rewarded first. A vote, a comment or just a read can make someone's day. 🐝</p>
<div class="upd" id="upd"><span>🕐 <b>Last update:</b> <span id="when"></span></span><span class="ago" id="ago"></span><span id="scan"></span></div>
<div class="bar"><input id="q" type="search" placeholder="Search title or author…" aria-label="Search">
<select id="comm" aria-label="Community"><option value="">All communities</option></select>
<select id="age" aria-label="Post age"><option value="">Any age</option><option value="6">Under 6 hours</option><option value="12">Under 12 hours</option></select></div>
<div id="list"></div>
<footer>
<p><b>How Scout Bee chooses</b></p>
<ul>
<li>Top-level posts 1–15 hours old, in a community, with pending rewards at or below the median of the moment.</li>
<li>At least 300 words and a quality score: own photos, paragraphs, a personal voice. Generic explainers, news-style articles, hashtag or all-caps titles are left out.</li>
<li>The author is part of the hive: comments on other people's posts in the last week, reputation 30+.</li>
<li>Skipped: public blacklists and community mutes, flood posting, copied text, NSFW, declined payouts, anti-abuse downvotes, posts already linked by other newsletters.</li>
<li><b>Originality ✓</b>: a sentence of the post was searched on the web and found nowhere else. <b>⏳ not checked yet</b>: the check runs a few posts per hour.</li>
</ul>
<p>Updated every hour · data: <a href="https://hafsql.mahdiyari.info">HAFSQL</a> by mahdiyari · idea by antisocialist · open source and AI-generated (MIT): <a href="https://github.com/hiveb3/scoutbee">github.com/hiveb3/scoutbee</a></p>
<p>Made with 💛 by <a href="https://peakd.com/@hive3">@hive3</a> · 🐝 <a href="https://peakd.com/c/hive-170283">AIBees</a> · 🎮 <a href="https://hiveb3.github.io/beetris/">BeeTris</a> · 🗳️ <a href="https://vote.hive.uno/@hive3">Vote @hive3 as witness</a></p>
</footer></div>
<script>
const D = __DATA__;
const esc = s => String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const gen = new Date(D.generated);
function ago(ms){const m=Math.round(ms/60000);if(m<1)return"just now";if(m<60)return m+" min ago";const h=Math.floor(m/60);return h+" h "+(m%60)+" min ago"}
function tick(){
  document.getElementById("when").textContent = gen.toLocaleString(undefined,{dateStyle:"medium",timeStyle:"short"}) + " (your time) · " + D.generated.slice(11,16) + " UTC";
  const ms = Date.now() - gen, el = document.getElementById("ago");
  el.textContent = ago(ms); el.className = ms > 3*3600e3 ? "ago stale" : "ago";
  if (ms > 3*3600e3) el.textContent += " · the list may be out of date";
}
document.getElementById("scan").textContent = D.posts.length + " posts shown · " + (D.window||0).toLocaleString() + " scanned";
const cs = [...new Set(D.posts.map(p => p.ct))].sort();
const sel = document.getElementById("comm"); cs.forEach(c => { const o=document.createElement("option"); o.value=o.textContent=c; sel.appendChild(o); });
function render(){
  const q = document.getElementById("q").value.toLowerCase(), c = sel.value, a = +document.getElementById("age").value || 1e9;
  const rows = D.posts.filter(p => (!q || (p.t+" "+p.a).toLowerCase().includes(q)) && (!c || p.ct===c) && (Date.now()-new Date(p.cr))/3600e3 <= a);
  document.getElementById("list").innerHTML = rows.length ? rows.map(p => {
    const h = Math.max(0, Math.round((Date.now()-new Date(p.cr))/3600e3)), path = "/" + p.c + "/@" + p.a + "/" + p.p;
    return `<div class="card"><h2><a href="https://peakd.com${esc(path)}" target="_blank" rel="noopener">${esc(p.t)}</a></h2>
    <div class="meta">🌱 <a href="https://peakd.com/@${esc(p.a)}" target="_blank" rel="noopener">${esc(p.a)}</a> · ${esc(p.ct)} · ${p.w.toLocaleString()} words${p.i?" · 📷":""} · ${h}h old · pending $${p.pend.toFixed(2)} · ${p.v} vote${p.v===1?"":"s"}</div>
    <div class="row"><a class="btn" href="https://peakd.com${esc(path)}" target="_blank" rel="noopener">PeakD</a>
    <a class="btn" href="https://ecency.com${esc(path)}" target="_blank" rel="noopener">Ecency</a>
    <a class="btn" href="https://inleo.io/@${esc(p.a)}/${esc(p.p)}" target="_blank" rel="noopener">InLeo</a>
    <span class="badge ${p.o==="ok"?"ok":"un"}">${p.o==="ok"?"Originality ✓":"⏳ not checked yet"}</span></div></div>`;
  }).join("") : '<p class="empty">No posts match these filters.</p>';
}
["q","comm","age"].forEach(id => document.getElementById(id).addEventListener("input", render));
tick(); render(); setInterval(tick, 30000);
</script></body></html>
"""
open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(page.replace("__DATA__", json.dumps(dict(
    generated=gen, posts=data, window=stats.get("window")), ensure_ascii=False).replace("</", "<\\/")))
print("site:", os.path.join(SITE, "index.html"), len(data), "posts, generated", gen)
