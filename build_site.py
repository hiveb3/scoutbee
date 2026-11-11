#!/usr/bin/env python3
# Open source (MIT) · AI-generated with Claude (Anthropic), reviewed by a human · https://github.com/hiveb3/scoutbee
# Scout Bee - builds the Wildflower Watch web page from scout.py output.
# Usage: python3 build_site.py OUTDIR SITEDIR   (OUTDIR has candidates.json + stats.json)  -> SITEDIR/index.html, SITEDIR/data.json
import sys, os, json, html, datetime as dt
BADGE = os.environ.get("WW_BADGE", "")   # URL of the small Wildflower Watch image added to comments (empty = text only)

OUT, SITE = sys.argv[1], sys.argv[2]
os.makedirs(SITE, exist_ok=True)
posts = json.load(open(os.path.join(OUT, "candidates.json")))
stats = json.load(open(os.path.join(OUT, "stats.json")))
gen = stats.get("generated") or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
skipped = sum(stats.get("why", {}).values())

data = [dict(t=p.get("t") or "(untitled)", a=p["a"], p=p["p"], c=p.get("cat", ""), ct=p.get("ctitle") or p.get("cat", ""),
             w=p.get("nw", 0), i=p.get("imgs", 0), cr=p["created"] + "Z", pend=round(p.get("pending", 0), 2),
             v=p.get("votes", 0), o=p.get("orig", "unchecked"), s=p.get("score", 0), fp=p.get("fp", 0), tk=p.get("talk", 0)) for p in posts]
json.dump(dict(generated=gen, posts=data, window=stats.get("window"), skipped=skipped, median=stats.get("median")),
          open(os.path.join(SITE, "data.json"), "w"), ensure_ascii=False)

page = r"""<!doctype html>
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
.top{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap}
.login{font-size:14px}.login button,.det button{font:inherit;padding:6px 12px;border-radius:8px;border:1px solid var(--honey);background:var(--honey);color:#2a1d00;cursor:pointer}
.login button.ghost,.det button.ghost{background:transparent;color:var(--fg)}
.det{margin-top:10px;border-top:1px dashed var(--line);padding-top:10px;font-size:14px}
.det .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:6px 12px;margin:6px 0}
.det .k{color:var(--muted)}.det .prev{background:var(--honey-soft);border-radius:8px;padding:8px 10px;margin:8px 0;white-space:pre-wrap;max-height:180px;overflow:auto}
.det img.cov{max-width:100%;max-height:220px;border-radius:8px;display:block;margin:6px 0}
.det textarea{width:100%;min-height:80px;padding:8px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--fg);font:inherit}
.det input[type=range]{width:160px;vertical-align:middle}.msg{font-size:13px;margin-left:6px}
footer{color:var(--muted);font-size:14px;border-top:1px solid var(--line);margin-top:22px;padding-top:12px}
footer a{color:var(--honey)}footer li{margin:2px 0}
</style></head><body><div class="wrap">
<div class="top"><h1>🌼 Wildflower Watch</h1><div class="login" id="login"></div></div>
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
<li><b>Vote and comment from here</b>: log in with Hive Keychain (browser extension or the Keychain mobile app). Nothing is stored on a server: your keys never leave Keychain.</li>
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
    <span class="badge ${p.o==="ok"?"ok":"un"}">${p.o==="ok"?"Originality ✓":"⏳ not checked yet"}</span>
    <button class="btn" style="background:none;cursor:pointer;font:inherit" data-k="${esc(p.a+"/"+p.p)}">Details · vote · comment ▾</button></div>
    <div class="det" id="d-${esc((p.a+"-"+p.p).replace(/[^a-z0-9-]/g,"-"))}" hidden></div></div>`;
  }).join("") : '<p class="empty">No posts match these filters.</p>';
}
["q","comm","age"].forEach(id => document.getElementById(id).addEventListener("input", render));
// ---------- login, details, vote, comment (Hive Keychain) ----------
const BADGE = __BADGE__;
const API = ["https://api.hive.blog", "https://api.deathwing.me", "https://api.openhive.network"];
async function rpc(method, params){ for (const u of API){ try{ const r = await fetch(u,{method:"POST",body:JSON.stringify({jsonrpc:"2.0",method,params,id:1})}).then(r=>r.json()); if (r.result!==undefined) return r.result; }catch(e){} } return null; }
let user = null; try { user = localStorage.getItem("ww_user"); } catch(e) {}
const kc = () => window.hive_keychain;
function drawLogin(){
  const el = document.getElementById("login");
  if (user) { el.innerHTML = `🐝 <b>@${esc(user)}</b> <button class="ghost" id="lo">Log out</button>`; document.getElementById("lo").onclick = () => { user=null; try{localStorage.removeItem("ww_user")}catch(e){} drawLogin(); }; }
  else { el.innerHTML = `<button id="li">Log in with Keychain</button>`; document.getElementById("li").onclick = login; }
}
function login(){
  if (!kc()) { alertBox("Hive Keychain not found. Install the browser extension or open this page in the Keychain mobile app."); return; }
  const name = (prompt("Your Hive username:") || "").trim().replace(/^@/,"").toLowerCase(); if (!name) return;
  kc().requestSignBuffer(name, "Log in to Wildflower Watch " + Date.now(), "Posting", r => {
    if (r.success) { user = name; try{localStorage.setItem("ww_user", name)}catch(e){} drawLogin(); } else alertBox("Login cancelled.");
  });
}
function alertBox(t){ const b=document.createElement("div"); b.className="upd"; b.textContent=t; document.querySelector(".wrap").prepend(b); setTimeout(()=>b.remove(),6000); }
function left(ts){ const ms = new Date(ts+"Z") - Date.now(); if (ms<=0) return "paid out"; const h=Math.floor(ms/3600e3); return h>=24? Math.floor(h/24)+" d "+(h%24)+" h":h+" h "+Math.floor(ms%3600e3/60000)+" min"; }
document.getElementById("list").addEventListener("click", async ev => {
  const b = ev.target.closest("button[data-k]"); if (!b) return;
  const [a, p] = b.dataset.k.split("/"), box = document.getElementById("d-"+(a+"-"+p).replace(/[^a-z0-9-]/g,"-"));
  if (!box.hidden) { box.hidden = true; return; }
  box.hidden = false; box.textContent = "Loading…";
  const P = D.posts.find(x => x.a===a && x.p===p) || {};
  const [post, prof] = await Promise.all([rpc("bridge.get_post",{author:a,permlink:p}), rpc("bridge.get_profile",{account:a})]);
  if (!post) { box.textContent = "Could not load the post, try again."; return; }
  const txt = (post.body||"").replace(/!\[[^\]]*\]\([^)]*\)/g,"").replace(/<[^>]+>/g," ").replace(/\[([^\]]*)\]\([^)]*\)/g,"$1").replace(/https?:\/\/\S+/g,"").replace(/[#*_>`]/g,"").replace(/\n{3,}/g,"\n\n").trim().slice(0,700);
  const img = (post.json_metadata && post.json_metadata.image || [])[0];
  const voted = user && (post.active_votes||[]).some(v => v.voter===user);
  const st = prof && prof.stats || {};
  box.innerHTML = `${img?`<img class="cov" src="https://images.hive.blog/640x0/${esc(img)}" alt="" loading="lazy">`:""}
   <div class="prev">${esc(txt)}${(post.body||"").length>700?"…":""}</div>
   <div class="grid">
    <div><span class="k">Author:</span> @${esc(a)} · rep ${prof?Math.round(prof.reputation):"?"}</div>
    <div><span class="k">Followers:</span> ${(st.followers||0).toLocaleString()} · posts ${(prof&&prof.post_count||0).toLocaleString()}</div>
    <div><span class="k">On Hive since:</span> ${prof?esc((prof.created||"").slice(0,10)):"?"}</div>
    <div><span class="k">Comments to others (7 days):</span> ${P.tk||0}</div>
    <div><span class="k">Pending now:</span> $${esc(post.pending_payout_value||"0").replace(" HBD","")}</div>
    <div><span class="k">Votes:</span> ${(post.active_votes||[]).filter(v=>v.rshares>0).length} · replies ${post.children||0}</div>
    <div><span class="k">Payout in:</span> ${esc(left(post.payout_at||post.cashout_time||""))}</div>
    <div><span class="k">Quality score:</span> ${P.s||"?"} · personal voice ${P.fp||0}/100 words</div>
   </div>
   <div class="row">${voted?`<span class="badge ok">You already voted ✓</span>`:`<label>Vote weight <input type="range" min="1" max="100" value="50" class="w"> <b class="wv">50%</b></label> <button class="vb">👍 Vote</button>`}<span class="msg vm"></span></div>
   <div style="margin-top:8px"><textarea class="ct" placeholder="Write a comment for ${esc(a)}…"></textarea>
   <label style="font-size:13px"><input type="checkbox" class="sig" checked> add a small "found via Wildflower Watch" signature</label>
   <div class="row"><button class="cb">💬 Comment</button><span class="msg cm"></span></div></div>`;
  const w = box.querySelector(".w"); if (w) w.oninput = () => box.querySelector(".wv").textContent = w.value+"%";
  const need = () => { if (!user) { alertBox("Log in first (button at the top)."); return false; } if (!kc()) { alertBox("Hive Keychain not found."); return false; } return true; };
  const vb = box.querySelector(".vb"); if (vb) vb.onclick = () => { if (!need()) return;
    kc().requestVote(user, p, a, +w.value*100, r => { box.querySelector(".vm").textContent = r.success ? "Voted ✓ thank you!" : "Vote cancelled or failed."; }); };
  box.querySelector(".cb").onclick = () => { if (!need()) return;
    let body = box.querySelector(".ct").value.trim(); if (!body) { box.querySelector(".cm").textContent = "Write something first."; return; }
    if (box.querySelector(".sig").checked) body += "\n\n" + (BADGE ? `[![Wildflower Watch](${BADGE})](https://hiveb3.github.io/scoutbee/)\n` : "") + "<sub>🌼 Found via [Wildflower Watch](https://hiveb3.github.io/scoutbee/)</sub>";
    const perm = ("re-" + a + "-" + Date.now().toString(36)).toLowerCase().replace(/[^a-z0-9-]/g,"");
    const op = ["comment", {parent_author:a, parent_permlink:p, author:user, permlink:perm, title:"", body,
                json_metadata:JSON.stringify({app:"wildflowerwatch/1.0", tags:["wildflowerwatch"]})}];
    kc().requestBroadcast(user, [op], "Posting", r => { box.querySelector(".cm").textContent = r.success ? "Comment published ✓" : "Comment cancelled or failed."; if (r.success) box.querySelector(".ct").value=""; });
  };
});
drawLogin();
tick(); render(); setInterval(tick, 30000);
</script></body></html>
"""
open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(page.replace("__BADGE__", json.dumps(BADGE)).replace("__DATA__", json.dumps(dict(
    generated=gen, posts=data, window=stats.get("window")), ensure_ascii=False).replace("</", "<\\/")))
print("site:", os.path.join(SITE, "index.html"), len(data), "posts, generated", gen)
