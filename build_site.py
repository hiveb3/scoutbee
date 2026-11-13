#!/usr/bin/env python3
# Open source (MIT) · AI-generated with Claude (Anthropic), reviewed by a human · https://github.com/hiveb3/scoutbee
# Scout Bee - builds the Wildflower Watch web page from scout.py output.
# Usage: python3 build_site.py OUTDIR SITEDIR   (OUTDIR has candidates.json + stats.json)  -> SITEDIR/index.html, SITEDIR/data.json
import sys, os, json, html, datetime as dt
BADGE = os.environ.get("WW_BADGE", "https://files.peakd.com/file/peakd-hive/scoutbee/23tv8FN1R9BH4SXFPSPyWsC98xP8A6q7AvysRLoTGQwrT8hHgF8cYegcT9MKpSRockEVJ.png")   # small Wildflower Watch image added to comments

OUT, SITE = sys.argv[1], sys.argv[2]
# page translations: one file per language in i18n/ (en.json is the reference, missing keys fall back to it)
I18N_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n")
I18N = {f[:-5]: json.load(open(os.path.join(I18N_DIR, f), encoding="utf-8")) for f in sorted(os.listdir(I18N_DIR)) if f.endswith(".json")}
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
.card.cur{opacity:.55;filter:grayscale(.8)}.card.cur:hover,.card.cur:focus-within{opacity:.9;filter:none}
.card.lowrc{border-left:5px solid #c62828}.badge.low{color:#c62828;border-color:#c62828;font-weight:700}
.curnote{font-size:13px;color:var(--muted);margin-top:6px;font-weight:600}
.top{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap}
.login{font-size:14px}.login button,.det button{font:inherit;padding:6px 12px;border-radius:8px;border:1px solid var(--honey);background:var(--honey);color:#2a1d00;cursor:pointer}
.login button.ghost,.det button.ghost{background:transparent;color:var(--fg)}
.det{margin-top:10px;border-top:1px dashed var(--line);padding-top:10px;font-size:14px}
.det .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:6px 12px;margin:6px 0}
.det .k{color:var(--muted)}.det .prev{background:var(--honey-soft);border-radius:8px;padding:8px 10px;margin:8px 0;white-space:pre-wrap;max-height:260px;overflow:auto}
.det img.cov{max-width:100%;max-height:220px;border-radius:8px;display:block;margin:6px 0}
.box{border:1px solid var(--line);border-radius:10px;padding:8px 10px;margin:8px 0}.box h3{font-size:14px;margin:0 0 4px}.box ul{margin:4px 0 0;padding-left:18px}
.rcbar{height:10px;border-radius:99px;background:var(--line);overflow:hidden;margin:4px 0}.rcbar i{display:block;height:100%;background:var(--ok)}
.tips{font-size:13px;white-space:pre-wrap;color:var(--muted)}
.thumbs{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}.thumbs img{width:72px;height:72px;object-fit:cover;border-radius:6px;border:1px solid var(--line);display:block}
.det textarea{width:100%;min-height:80px;padding:8px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--fg);font:inherit}
.det input[type=range]{width:160px;vertical-align:middle}.msg{font-size:13px;margin-left:6px}
footer{color:var(--muted);font-size:14px;border-top:1px solid var(--line);margin-top:22px;padding-top:12px}
footer a{color:var(--honey)}footer li{margin:2px 0}
</style></head><body><div class="wrap">
<div class="top"><h1>🌼 Wildflower Watch</h1><div class="login"><select id="lang" aria-label="Language" style="font:inherit;padding:5px 6px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--fg)"></select> <span id="login"></span></div></div>
<p class="sub" data-i18n="sub"></p>
<div class="upd" id="upd"><span>🕐 <b data-i18n="last_update"></b> <span id="when"></span></span><span class="ago" id="ago"></span><span id="scan"></span><button id="rf" hidden style="font:inherit;font-weight:700;padding:6px 12px;border-radius:8px;border:1px solid var(--honey);background:var(--honey);color:#2a1d00;cursor:pointer"></button></div>
<div class="bar"><input id="q" type="search" data-i18n-ph="search_ph" placeholder="Search title or author…" aria-label="Search">
<select id="comm" aria-label="Community"><option value="" data-i18n="all_comm"></option></select>
<select id="age" aria-label="Post age"><option value="" data-i18n="any_age"></option><option value="6" data-i18n="under6"></option><option value="12" data-i18n="under12"></option></select></div>
<div id="list"></div>
<footer>
<p><b data-i18n="how_title"></b></p>
<ul><li data-i18n="f1"></li><li data-i18n="f2"></li><li data-i18n="f3"></li><li data-i18n="f4"></li><li data-i18n="f5"></li><li data-i18n="f6"></li><li data-i18n="f7"></li></ul>
<p>Updated every hour · data: <a href="https://hafsql.mahdiyari.info">HAFSQL</a> by mahdiyari · idea by antisocialist · trust, health and RC checks inspired by the <a href="https://tools.botlord.eu/">botlord toolbox</a> · open source and AI-generated (MIT): <a href="https://github.com/hiveb3/scoutbee">github.com/hiveb3/scoutbee</a></p>
<p>Made with 💛 by <a href="https://peakd.com/@hive3">@hive3</a> · 🐝 <a href="https://peakd.com/c/hive-170283">AIBees</a> · 🎮 <a href="https://hiveb3.github.io/beetris/">BeeTris</a> · 🗳️ <a href="https://vote.hive.uno/@hive3">Vote @hive3 as witness</a></p>
</footer></div>
<script>
const D = __DATA__;
const I18N = __I18N__;
const LANGS = {en:"English",es:"Español",pt:"Português",it:"Italiano",de:"Deutsch",fr:"Français",pl:"Polski",nl:"Nederlands",uk:"Українська",ja:"日本語",zh:"中文",hi:"हिन्दी"};   // chosen from the Hive users-per-country and post-language ranking by @enrique89
let LANG = (() => { try { const s = localStorage.getItem("ww_lang"); if (s && I18N[s]) return s; } catch(e) {} const n = (navigator.language||"en").slice(0,2).toLowerCase(); return I18N[n] ? n : "en"; })();
function T(k, v){ v = v || {}; const s = (I18N[LANG] && I18N[LANG][k]) || I18N.en[k] || k; return s.replace(/\{(\w+)\}/g, (_, x) => v[x] !== undefined ? v[x] : "{"+x+"}"); }
const NUM = n => Number(n).toLocaleString(LANG);
function applyStatic(){
  document.documentElement.lang = LANG;
  document.querySelectorAll("[data-i18n]").forEach(e => { const v = e.dataset.v ? JSON.parse(e.dataset.v) : {};
    if (e.dataset.ym) v.month = new Date(e.dataset.ym + "-15").toLocaleDateString(LANG, {month:"long", year:"numeric"});
    e.innerHTML = T(e.dataset.i18n, v); });
  document.querySelectorAll("[data-i18n-ph]").forEach(e => e.placeholder = T(e.dataset.i18nPh));
}
const langSel = document.getElementById("lang");
Object.entries(LANGS).forEach(([k, n]) => { const o = document.createElement("option"); o.value = k; o.textContent = "🌐 " + n; langSel.appendChild(o); });
langSel.value = LANG;
langSel.onchange = () => { LANG = langSel.value; try { localStorage.setItem("ww_lang", LANG); } catch(e) {} applyStatic(); tick(); drawLogin(); render();
  Object.keys(RCP).forEach(a => setRC(a, RCP[a])); Object.keys(CUR).forEach(markCur); };
applyStatic();
const esc = s => String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const gen = new Date(D.generated);
function ago(ms){const m=Math.round(ms/60000);if(m<1)return T("ago_now");if(m<60)return T("ago_min",{m});const h=Math.floor(m/60);return T("ago_h",{h,m:m%60})}
function tick(){
  document.getElementById("when").textContent = gen.toLocaleString(LANG,{dateStyle:"medium",timeStyle:"short"}) + " " + T("your_time") + " · " + D.generated.slice(11,16) + " UTC";
  const ms = Date.now() - gen, el = document.getElementById("ago");
  el.textContent = ago(ms); el.className = ms > 3*3600e3 ? "ago stale" : "ago";
  if (ms > 3*3600e3) el.textContent += " · " + T("stale");
  const rf = document.getElementById("rf"); rf.hidden = !(ms > 3*3600e3); rf.textContent = RF[LANG] || RF.en;
}
const RF = {en:"🔄 Scout bee, refresh the page to gather fresh flowers!",it:"🔄 Ape esploratrice, ricarica la pagina per raccogliere fiori freschi!",es:"🔄 Abeja exploradora, ¡recarga la página para recoger flores frescas!",pt:"🔄 Abelha exploradora, atualize a página para colher flores frescas!",de:"🔄 Kundschafterbiene, lade die Seite neu und sammle frische Blüten!",fr:"🔄 Abeille éclaireuse, recharge la page pour cueillir des fleurs fraîches !",pl:"🔄 Pszczoło zwiadowczyni, odśwież stronę, by zebrać świeże kwiaty!",nl:"🔄 Verkennersbij, vernieuw de pagina en verzamel verse bloemen!",uk:"🔄 Бджоло-розвіднице, онови сторінку, щоб зібрати свіжі квіти!",ja:"🔄 偵察バチさん、ページを更新して新しい花を集めよう！",zh:"🔄 侦察蜂，刷新页面去采新鲜的花吧！",hi:"🔄 स्काउट मधुमक्खी, ताज़े फूल चुनने के लिए पेज रीफ़्रेश करें!"};
document.getElementById("rf").onclick = () => { const u = new URL(location.href); u.searchParams.set("t", Date.now()); location.replace(u.toString()); };

const cs = [...new Set(D.posts.map(p => p.ct))].sort();
const sel = document.getElementById("comm"); cs.forEach(c => { const o=document.createElement("option"); o.value=o.textContent=c; sel.appendChild(o); });
function render(){
  document.getElementById("scan").textContent = T("scan", {n: D.posts.length, s: NUM(D.window||0)});
  const q = document.getElementById("q").value.toLowerCase(), c = sel.value, a = +document.getElementById("age").value || 1e9;
  const rows = D.posts.filter(p => (!q || (p.t+" "+p.a).toLowerCase().includes(q)) && (!c || p.ct===c) && (Date.now()-new Date(p.cr))/3600e3 <= a);
  document.getElementById("list").innerHTML = rows.length ? rows.map(p => {
    const h = Math.max(0, Math.round((Date.now()-new Date(p.cr))/3600e3)), path = "/" + p.c + "/@" + p.a + "/" + p.p;
    const k = p.a+"/"+p.p, cu = CUR[k];
    const rc = RCP[p.a], low = rc !== undefined && rc < LOW_RC;
    return `<div class="card${cu?" cur":""}${low?" lowrc":""}" data-c="${esc(k)}" data-a="${esc(p.a)}"><h2><a href="https://peakd.com${esc(path)}" target="_blank" rel="noopener">${esc(p.t)}</a></h2>
    <div class="meta">🌱 <a href="https://peakd.com/@${esc(p.a)}" target="_blank" rel="noopener">${esc(p.a)}</a> · ${esc(p.ct)} · ${T("words",{n:NUM(p.w)})}${p.i?" · 📷":""} · ${T("old",{h})} · ${T("pending",{v:p.pend.toFixed(2)})} · ${T(p.v===1?"vote1":"votes",{n:p.v})}</div>
    <div class="row"><a class="btn" href="https://peakd.com${esc(path)}" target="_blank" rel="noopener">PeakD</a>
    <a class="btn" href="https://ecency.com${esc(path)}" target="_blank" rel="noopener">Ecency</a>
    <a class="btn" href="https://inleo.io/@${esc(p.a)}/${esc(p.p)}" target="_blank" rel="noopener">InLeo</a>
    <span class="badge ${p.o==="ok"?"ok":"un"}">${T(p.o==="ok"?"orig_ok":p.o==="suspect"?"orig_sus":"orig_un")}</span>
    <span class="badge rcb${low?" low":""}" ${rc===undefined?"hidden":""}>${rc===undefined?"":rcLabel(rc)}</span>
    <button class="btn" style="background:none;cursor:pointer;font:inherit" data-k="${esc(p.a+"/"+p.p)}">${T("details")}</button></div>
    <div class="curnote">${cu?curText(cu):""}</div>
    <div class="det" id="d-${esc((p.a+"-"+p.p).replace(/[^a-z0-9-]/g,"-"))}" hidden></div></div>`;
  }).join("") : '<p class="empty">' + T("empty") + '</p>';
}
["q","comm","age"].forEach(id => document.getElementById(id).addEventListener("input", render));
// ---------- authors with low Resource Credits (they can hardly comment or reply) ----------
const RCP = {}, LOW_RC = 20;
const rcLabel = v => T(v < LOW_RC ? "rc_low" : "rc") + " " + v.toFixed(0) + "%";
async function scanRC(){
  const names = [...new Set(D.posts.map(p => p.a))];
  const r = await rpc("rc_api.find_rc_accounts", {accounts: names}); if (!r) return;
  for (const x of r.rc_accounts || []) setRC(x.account, rcCalc(x).pct);
}
// ---------- already curated? (a comment with the Wildflower Watch signature) ----------
const CUR = {};
const curText = c => T("curated", {who: c.who, when: new Date(c.when + "Z").toLocaleString(LANG, {dateStyle:"medium", timeStyle:"short"})});
function markCur(k){ const card = document.querySelector(`.card[data-c="${CSS.escape(k)}"]`); if (!card || !CUR[k]) return;
  card.classList.add("cur"); card.querySelector(".curnote").textContent = curText(CUR[k]); }
async function scanCurated(){
  const keys = D.posts.map(p => p.a+"/"+p.p);
  for (let i = 0; i < keys.length; i += 5) await Promise.all(keys.slice(i, i+5).map(async k => {
    const [a, p] = k.split("/"); const rs = await rpc("condenser_api.get_content_replies", [a, p]) || [];
    const hit = rs.filter(r => (r.body||"").includes("hiveb3.github.io/scoutbee") || String(r.json_metadata||"").includes("wildflowerwatch"))
                  .sort((x, y) => x.created < y.created ? -1 : 1)[0];
    if (hit) { CUR[k] = {who: hit.author, when: hit.created}; markCur(k); }
  }));
}
// ---------- login, details, vote, comment (Hive Keychain) ----------
const BADGE = __BADGE__;
const API = ["https://api.hive.blog", "https://api.deathwing.me", "https://api.openhive.network"];
async function rpc(method, params){ for (const u of API){ try{ const r = await fetch(u,{method:"POST",body:JSON.stringify({jsonrpc:"2.0",method,params,id:1})}).then(r=>r.json()); if (r.result!==undefined) return r.result; }catch(e){} } return null; }
// account history filtered by operation type: the 64-bit filter is sent as an exact integer (JSON numbers would round it)
async function history(acc, low){ for (const u of API){ try{ const r = await fetch(u,{method:"POST",body:`{"jsonrpc":"2.0","method":"condenser_api.get_account_history","params":["${acc}",-1,1000,${low}],"id":1}`}).then(r=>r.json()); if (r.result!==undefined) return r.result; }catch(e){} } return null; }
const RC_COMMENT = 1.15e9;   // approx. RC cost of one comment
function rcCalc(x){ if (!x) return null; const max = +x.max_rc, m = x.rc_manabar;
  const cur = max ? Math.min(max, +m.current_mana + max * (Date.now()/1000 - m.last_update_time) / 432000) : 0;
  return {max, cur, pct: max ? cur / max * 100 : 0, recv: +(x.received_delegated_rc || 0)}; }
function rcInner(c){ if (!c) return "<h3>" + T("rc_meter_q") + "</h3>";
  return `<h3>${T("rc_meter",{p:c.pct.toFixed(0),n:NUM(Math.floor(c.cur/RC_COMMENT))})}</h3>
    <div class="rcbar"><i style="width:${Math.max(1,c.pct).toFixed(0)}%;${c.pct<20?"background:#c62828":c.pct<50?"background:var(--warn)":""}"></i></div>
    ${c.recv?`<div style="font-size:12px;color:var(--muted)">${T("rc_lent",{n:NUM(Math.floor(c.recv/RC_COMMENT))})}</div>`:""}`; }
function setRC(a, pct){ RCP[a] = pct; document.querySelectorAll(`.card[data-a="${CSS.escape(a)}"]`).forEach(card => {
  const s = card.querySelector(".rcb"); s.hidden = false; s.textContent = rcLabel(pct); s.classList.toggle("low", pct < LOW_RC); card.classList.toggle("lowrc", pct < LOW_RC); }); }
let user = null; try { user = localStorage.getItem("ww_user"); } catch(e) {}
const kc = () => window.hive_keychain;
function drawLogin(){
  const el = document.getElementById("login");
  if (user) { el.innerHTML = `🐝 <b>@${esc(user)}</b> <button class="ghost" id="lo">${T("logout")}</button>`; document.getElementById("lo").onclick = () => { user=null; try{localStorage.removeItem("ww_user")}catch(e){} drawLogin(); }; }
  else { el.innerHTML = `<button id="li">${T("login")}</button>`; document.getElementById("li").onclick = login; }
}
function login(){
  if (!kc()) { alertBox(T("no_kc")); return; }
  const name = (prompt(T("ask_user")) || "").trim().replace(/^@/,"").toLowerCase(); if (!name) return;
  kc().requestSignBuffer(name, "Log in to Wildflower Watch " + Date.now(), "Posting", r => {
    if (r.success) { user = name; try{localStorage.setItem("ww_user", name)}catch(e){} drawLogin(); } else alertBox(T("login_cancel"));
  });
}
function alertBox(t){ const b=document.createElement("div"); b.className="upd"; b.textContent=t; document.querySelector(".wrap").prepend(b); setTimeout(()=>b.remove(),6000); }
function left(ts){ const ms = new Date(ts+"Z") - Date.now(); if (ms<=0) return T("paid_out"); const h=Math.floor(ms/3600e3); return h>=24? Math.floor(h/24)+" d "+(h%24)+" h":h+" h "+Math.floor(ms%3600e3/60000)+" min"; }
document.getElementById("list").addEventListener("click", async ev => {
  const b = ev.target.closest("button[data-k]"); if (!b) return;
  const [a, p] = b.dataset.k.split("/"), box = document.getElementById("d-"+(a+"-"+p).replace(/[^a-z0-9-]/g,"-"));
  if (!box.hidden) { box.hidden = true; return; }
  box.hidden = false; box.textContent = T("loading");
  const P = D.posts.find(x => x.a===a && x.p===p) || {};
  const [post, prof, accs, rcs] = await Promise.all([rpc("bridge.get_post",{author:a,permlink:p}), rpc("bridge.get_profile",{account:a}),
    rpc("condenser_api.get_accounts",[[a]]), rpc("rc_api.find_rc_accounts",{accounts:[a]})]);
  const [dgp, hist] = await Promise.all([rpc("condenser_api.get_dynamic_global_properties",[]), history(a, "108086391056891904")]);
  const acc = (accs||[])[0] || {}, rca = (rcs && rcs.rc_accounts || [])[0];
  // ---- trust check (public data) ----
  const rep = prof ? prof.reputation : 25, yrs = prof && prof.created ? (Date.now() - new Date(prof.created+"Z")) / 31557600000 : 0;
  const shared = [...((acc.owner||{}).account_auths||[]), ...((acc.active||{}).account_auths||[])].map(x => x[0]);
  const TR = [[true, T("t_lists")],
             [rep >= 35, T(rep >= 50 ? "rep_strong" : rep >= 35 ? "rep_fair" : "rep_low", {r: rep.toFixed(1)})],
             [yrs >= .25, yrs >= 1 ? T("acc_est",{y:yrs.toFixed(1)}) : yrs >= .25 ? T("acc_young",{m:Math.round(yrs*12)}) : T("acc_new",{d:Math.round(yrs*365)})],
             [!shared.length, shared.length ? T("keys_shared",{list:"@"+shared.join(", @")}) : T("keys_ok")]];
  const flags = TR.filter(t => !t[0]).length;
  // ---- RC meter ----
  const rcc = rcCalc(rca), rcPct = rcc ? rcc.pct : null;
  // ---- power downs ----
  const hpPerVest = dgp ? parseFloat(dgp.total_vesting_fund_hive) / parseFloat(dgp.total_vesting_shares) : 0;
  const PD = [];
  const rate = parseFloat(acc.vesting_withdraw_rate || 0);
  if (rate > 0 && hpPerVest) {
    const leftW = Math.max(0, Math.round((acc.to_withdraw - acc.withdrawn) / 1e6 / rate));
    PD.push([false, T("pd_on",{hp:(rate*hpPerVest).toFixed(0),w:leftW,date:new Date(acc.next_vesting_withdrawal+"Z").toLocaleDateString(LANG)})]);
  } else if (acc.name) PD.push([true, T("pd_none")]);
  if (hist) {
    const yr = Date.now() - 365*864e5, fills = hist.map(h => h[1]).filter(o => o.op[0]==="fill_vesting_withdraw" && o.op[1].from_account===a && new Date(o.timestamp+"Z") > yr);
    const tot = fills.reduce((s, o) => s + parseFloat(o.op[1].deposited), 0);
    PD.push([fills.length===0, fills.length ? T("pd_12",{n:fills.length,h:tot.toFixed(0)}) : T("pd_12none")]);
  }
  // ---- account health tips for the author (optional, added to the comment) ----
  const tips = [];
  const unclaimed = [acc.reward_hbd_balance, acc.reward_hive_balance, acc.reward_vesting_hive].filter(x => x && parseFloat(x) > 0);
  if (unclaimed.length) tips.push(T("tip_claim",{x:unclaimed.join(", ").replace("VESTS","").trim()}));
  if (rcPct !== null && rcPct < 20) tips.push(T("tip_rc",{p:rcPct.toFixed(0)}));
  if (!acc.proxy && (acc.witness_votes||[]).length) {
    const ws = await Promise.all(acc.witness_votes.slice(0,30).map(w => rpc("condenser_api.get_witness_by_account",[w])));
    const off = ws.filter(w => w && /^STM1{20}/.test(w.signing_key)).map(w => w.owner);
    if (off.length) tips.push(T("tip_wit",{n:off.length,list:off.map(x=>"@"+x).join(", ")}));
  } else if (!acc.proxy && acc.name) tips.push(T("tip_nowit"));
  if (!post) { box.textContent = T("no_post"); return; }
  const txt = (post.body||"").replace(/!\[[^\]]*\]\([^)]*\)/g,"").replace(/<[^>]+>/g," ").replace(/\[([^\]]*)\]\([^)]*\)/g,"$1").replace(/https?:\/\/\S+/g,"").replace(/[#*_>`]/g,"").replace(/\n{3,}/g,"\n\n").trim();
  const imgs = [...new Set([...(post.json_metadata && post.json_metadata.image || []),
    ...[...(post.body||"").matchAll(/https?:\/\/[^\s)"'<>\]]+?\.(?:jpe?g|png|gif|webp)(?:\?[^\s)"'<>]*)?/gi)].map(m => m[0]),
    ...[...(post.body||"").matchAll(/!\[[^\]]*\]\((https?:\/\/[^\s)]+)\)/g)].map(m => m[1])])].filter(u => /^https?:\/\//.test(u));
  const img = imgs[0];
  const SAY = [T("say1"), T("say2"), T("say3"), T("say4")];
  const voted = user && (post.active_votes||[]).some(v => v.voter===user);
  const st = prof && prof.stats || {};
  box.innerHTML = `${img?`<img class="cov" src="https://images.hive.blog/640x0/${esc(img)}" alt="" loading="lazy">`:""}
   ${imgs.length>1?`<div class="thumbs">${imgs.slice(1,25).map(u=>`<a href="${esc(u)}" target="_blank" rel="noopener"><img src="https://images.hive.blog/144x144/${esc(u)}" alt="" loading="lazy"></a>`).join("")}</div>`:""}
   <div class="prev">${esc(txt)}</div>
   <div class="grid">
    <div><span class="k">${T("k_author")}</span> @${esc(a)} · ${T("rep")} ${prof?Math.round(prof.reputation):"?"}</div>
    <div><span class="k">${T("k_followers")}</span> ${NUM(st.followers||0)} · ${T("posts")} ${NUM(prof&&prof.post_count||0)}</div>
    <div><span class="k">${T("k_since")}</span> ${prof?esc((prof.created||"").slice(0,10)):"?"}</div>
    <div><span class="k">${T("k_talk")}</span> ${P.tk||0}</div>
    <div><span class="k">${T("k_pending")}</span> $${esc(post.pending_payout_value||"0").replace(" HBD","")}</div>
    <div><span class="k">${T("k_votes")}</span> ${(post.active_votes||[]).filter(v=>v.rshares>0).length} · ${T("replies")} ${post.children||0}</div>
    <div><span class="k">${T("k_payout")}</span> ${esc(left(post.payout_at||post.cashout_time||""))}</div>
    <div><span class="k">${T("k_quality")}</span> ${P.s||"?"} · ${T("voice",{n:P.fp||0})}</div>
   </div>
   <div class="box"><h3>${T("trust_title")} ${flags ? T("trust_review",{n:flags}) : T("trust_ok")}</h3><ul>${TR.map(t=>`<li>${t[0]?"🟢":"🟡"} ${esc(t[1])}</li>`).join("")}</ul></div>
   ${PD.length?`<div class="box"><h3>${T("pd_title")}</h3><ul>${PD.map(t=>`<li>${t[0]?"🟢":"🟡"} ${esc(t[1])}</li>`).join("")}</ul></div>`:""}
   <div class="box"><div class="rcin">${rcInner(rcc)}</div>
    <div class="row"><span style="font-size:13px">${T("give_rc",{a:esc(a)})}</span> <button class="rcd ghost" data-n="25">${T("rc_n",{n:25})}</button> <button class="rcd ghost" data-n="100">${T("rc_n",{n:100})}</button> <button class="rcd ghost" data-n="0">${T("rc_rm")}</button><span class="msg rm"></span></div>
    <div style="font-size:12px;color:var(--muted)">${T("rc_note")}</div></div>
   <div class="row" style="font-size:13px">${T("deeper")} ${[["🛡️ Trust","trust"],["🚩 Flags","flags"],["🩺 Health","health"]].map(([l,s])=>`<a class="btn" href="https://${s}.botlord.eu/?u=${esc(a)}" target="_blank" rel="noopener">${l}</a>`).join(" ")}</div>
   ${tips.length?`<div class="box"><h3>${T("tips_title")}</h3><div class="tips">${esc(tips.join("\n"))}</div>
    <label style="font-size:13px"><input type="checkbox" class="tip"> ${T("tips_add")}</label></div>`:""}
   <div class="row">${voted?`<span class="badge ok">${T("voted")}</span>`:`<label>${T("weight")} <input type="range" min="1" max="100" value="50" class="w"> <b class="wv">50%</b></label> <button class="vb">${T("vote_btn")}</button>`}<span class="msg vm"></span></div>
   <div style="margin-top:8px"><textarea class="ct" placeholder="${T("comment_ph",{a:esc(a)})}">${user?esc(SAY[Math.floor(Math.random()*SAY.length)]+"\n\n"):""}</textarea>
   <label style="font-size:13px">${CUR[a+"/"+p]?`<input type="checkbox" class="sig" disabled> ${T("sig_done",{who:esc(CUR[a+"/"+p].who)})}`:`<input type="checkbox" class="sig" checked> ${T("sig_add")}`}</label>
   <div class="row"><button class="cb">${T("comment_btn")}</button><span class="msg cm"></span></div></div>`;
  box.querySelectorAll(".rcd").forEach(btn => btn.onclick = () => { if (!need()) return;
    const n = Math.round(+btn.dataset.n * RC_COMMENT);
    kc().requestCustomJson(user, "rc", "Posting", JSON.stringify(["delegate_rc", {from:user, delegatees:[a], max_rc:n}]),
      n ? `Delegate ≈${btn.dataset.n} comments of RC to @${a}` : `Remove your RC delegation to @${a}`,
      r => { box.querySelector(".rm").textContent = r.success ? T(n ? "rc_ok" : "rc_rm_ok") : T("cancelled");
        if (!r.success) return;
        const ct = box.querySelector(".ct"), line = /\n?⚡ [^\n]*RC[^\n]*\n?|\n?⚡ I also lent you[^\n]*\n?/;
        ct.value = ct.value.replace(line, "\n");
        if (n) ct.value = ct.value.replace(/\s*$/, "") + "\n" + T("rc_line",{n:btn.dataset.n}) + "\n\n";
        setTimeout(async () => { const x = await rpc("rc_api.find_rc_accounts",{accounts:[a]}); const c = rcCalc(x && x.rc_accounts && x.rc_accounts[0]);
          if (!c) return; box.querySelector(".rcin").innerHTML = rcInner(c); setRC(a, c.pct);
          const i = tips.findIndex(t => t.startsWith("⚡")); if (i < 0) return;
          if (c.pct >= 20) tips.splice(i, 1); else tips[i] = tips[i].replace(/\(\d+%\)/, `(${c.pct.toFixed(0)}%)`);
          const tb = box.querySelector(".tips"); if (tb) { tb.textContent = tips.join("\n"); if (!tips.length) tb.parentElement.remove(); } }, 4000); }); });
  const w = box.querySelector(".w"); if (w) w.oninput = () => box.querySelector(".wv").textContent = w.value+"%";
  const need = () => { if (!user) { alertBox(T("login_first")); return false; } if (!kc()) { alertBox(T("no_kc")); return false; } return true; };
  const vb = box.querySelector(".vb"); if (vb) vb.onclick = () => { if (!need()) return;
    kc().requestVote(user, p, a, +w.value*100, r => { box.querySelector(".vm").textContent = r.success ? T("vote_ok") : T("vote_fail"); }); };
  box.querySelector(".cb").onclick = () => { if (!need()) return;
    let body = box.querySelector(".ct").value.trim(); if (!body) { box.querySelector(".cm").textContent = T("write_first"); return; }
    const tp = box.querySelector(".tip"); if (tp && tp.checked) body += "\n\n<sub>" + T("tips_head") + "</sub>\n" + tips.map(t => "- " + t).join("\n");
    if (box.querySelector(".sig").checked) body += "\n\n" + (BADGE ? `[![Wildflower Watch](${BADGE})](https://hiveb3.github.io/scoutbee/)\n` : "") + "<sub>🌼 " + T("found_via") + " [Wildflower Watch](https://hiveb3.github.io/scoutbee/)</sub>";
    const perm = ("re-" + a + "-" + Date.now().toString(36)).toLowerCase().replace(/[^a-z0-9-]/g,"");
    const op = ["comment", {parent_author:a, parent_permlink:p, author:user, permlink:perm, title:"", body,
                json_metadata:JSON.stringify({app:"wildflowerwatch/1.0", tags:["wildflowerwatch"]})}];
    kc().requestBroadcast(user, [op], "Posting", r => { box.querySelector(".cm").textContent = r.success ? T("com_ok") : T("com_fail"); if (r.success) { box.querySelector(".ct").value=""; if (!CUR[a+"/"+p] && box.querySelector(".sig").checked) { CUR[a+"/"+p] = {who:user, when:new Date().toISOString().slice(0,19)}; markCur(a+"/"+p); } } });
  };
});
drawLogin();
tick(); render(); setInterval(tick, 30000); scanRC(); scanCurated();
</script></body></html>
"""
open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(page.replace("__I18N__", json.dumps(I18N, ensure_ascii=False).replace("</", "<\\/")).replace("__BADGE__", json.dumps(BADGE)).replace("__DATA__", json.dumps(dict(
    generated=gen, posts=data, window=stats.get("window")), ensure_ascii=False).replace("</", "<\\/")))
if os.path.exists("state/checked.json"):       # shared anti-plagiarism cache: the weekly run reuses it instead of searching again
    import shutil; shutil.copy("state/checked.json", os.path.join(SITE, "checked.json"))
print("site:", os.path.join(SITE, "index.html"), len(data), "posts, generated", gen)
# 🏆 Wildflower Cup leaderboard: added to the page right here, so the hourly workflow needs no extra step
import subprocess
subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaderboard.py"), SITE])
