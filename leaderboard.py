#!/usr/bin/env python3
# Open source (MIT) · AI-generated with Claude (Anthropic), reviewed by a human · https://github.com/hiveb3/scoutbee
# Scout Bee - curators leaderboard: who curated the most Wildflower Watch posts and how much reward their votes gave.
# A post counts as curated by someone when they commented it with the Wildflower Watch signature.
# The whole history (since SINCE) is rebuilt on every run, so the board is always complete.
# Usage: python3 leaderboard.py SITEDIR   (after build_site.py) -> SITEDIR/leaderboard.json + a 🏆 section in SITEDIR/index.html
import sys, os, json, html, datetime as dt, urllib.request

SINCE = dt.datetime(2026, 11, 1)            # Wildflower Watch went live in November 2026
TEAM = {"hive3", "scoutbee", "pollenpatron", "beecounter", "hiveb3", "beetris.contest", "hivethree", "hive-170283",
        "hive3.guard", "hive-3", "hive2bee3", "hive.bee-3", "bz3", "aibees", "ai-bee"}   # our own accounts: ranked too, marked 🐝
NODES = ["https://api.hive.blog", "https://api.deathwing.me", "https://api.openhive.network"]

def rpc(method, params):
    for n in NODES * 2:
        try:
            req = urllib.request.Request(n, headers={"Content-Type": "application/json"},
                  data=json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode())
            r = json.load(urllib.request.urlopen(req, timeout=20))
            if "result" in r: return r["result"]
        except Exception as e:
            print("rpc retry", method, e, flush=True)
    raise RuntimeError("rpc failed: " + method)

def main(out):
    import psycopg2
    con = psycopg2.connect(host="hafsql-sql.mahdiyari.info", port=5432, dbname="haf_block_log",
                           user="hafsql_public", password="hafsql_public", connect_timeout=30)
    cur = con.cursor()
    cur.execute("""SELECT author, parent_author, parent_permlink, created FROM hafsql.comments
                   WHERE parent_author <> '' AND created >= %s
                     AND (body LIKE '%%hiveb3.github.io/scoutbee%%' OR json_metadata::text LIKE '%%wildflowerwatch%%')""", (SINCE,))
    rows = cur.fetchall(); con.close()
    # $ value of one rshare: reward pool / recent claims x HIVE price
    rf = rpc("condenser_api.get_reward_fund", ["post"])
    pr = rpc("condenser_api.get_current_median_history_price", [])
    usd = float(rf["reward_balance"].split()[0]) / float(rf["recent_claims"]) * float(pr["base"].split()[0]) / float(pr["quote"].split()[0])
    now = dt.datetime.utcnow(); month0 = dt.datetime(now.year, now.month, 1)
    posts = {}                                                     # (author, permlink) -> {curator: first signed comment time}
    for c, a, p, t in rows:
        if c == a: continue                                        # no self-curation
        t = t.replace(tzinfo=None) if getattr(t, "tzinfo", None) else t
        d = posts.setdefault((a, p), {}); d[c] = min(d.get(c, t), t)
    allb, monb = {}, {}
    for (a, p), curs in posts.items():
        try: votes = {v["voter"]: v for v in rpc("condenser_api.get_active_votes", [a, p])}
        except Exception: votes = {}
        first = min(curs.values())
        # our accounts count also when they only voted a curated post (e.g. the @scoutbee / @pollenpatron trail)
        for t in TEAM:
            if t in votes and t != a and t not in curs and int(votes[t]["rshares"]) > 0: curs[t] = first
        for c, t in curs.items():
            v = votes.get(c); val = int(v["rshares"]) * usd if v and int(v["rshares"]) > 0 else 0.0
            for board, ok in ((allb, True), (monb, t >= month0)):
                if not ok: continue
                b = board.setdefault(c, {"curator": c, "posts": 0, "voted": 0, "rewards": 0.0, "team": c in TEAM})
                b["posts"] += 1; b["voted"] += 1 if val else 0; b["rewards"] += val
    def rank(board):
        r = sorted(board.values(), key=lambda x: (-x["posts"], -x["rewards"]))
        for b in r: b["rewards"] = round(b["rewards"], 3)
        return r
    lb = {"generated": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "month": month0.strftime("%B %Y"), "ym": month0.strftime("%Y-%m"),
          "posts": len(posts), "total_rewards": round(sum(b["rewards"] for b in allb.values()), 3),
          "month_posts": sum(1 for curs in posts.values() if min(curs.values()) >= month0),
          "curators": rank(allb), "contest": rank(monb),
          "contest_rewards": sorted(rank(monb), key=lambda x: (-x["rewards"], -x["posts"]))}
    json.dump(lb, open(os.path.join(out, "leaderboard.json"), "w"), indent=1)
    print("leaderboard:", len(lb["curators"]), "curators,", len(posts), "curated posts", flush=True)
    inject(out, lb)

CSS = """<style>.board{margin-top:26px}.board h2{margin:0 0 4px}.board table{width:100%;border-collapse:collapse;font-size:15px}
.board th,.board td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line)}.board th{color:var(--muted);font-weight:600}
.board td:nth-child(n+3),.board th:nth-child(n+3){text-align:right}.board a{color:var(--honey)}.board .note{font-size:13px;color:var(--muted)}</style>"""

def table(rows, podium, need_rewards=False):
    out, place = "", 0
    for i, c in enumerate(rows[:20]):
        medal = ""
        if podium and not c["team"] and place < 3 and (c["rewards"] > 0 or not need_rewards): medal = "🥇🥈🥉"[place]; place += 1
        who = html.escape(c["curator"])
        out += (f'<tr><td>{medal or i + 1}</td><td><a href="https://peakd.com/@{who}" target="_blank" rel="noopener">@{who}</a>{" 🐝" if c["team"] else ""}</td>'
                f'<td>{c["posts"]}</td><td>{c["voted"]}</td><td>${c["rewards"]:.2f}</td></tr>')
    head = ('<table><thead><tr><th>#</th><th data-i18n="th_cur">Curator</th><th data-i18n="th_posts">Posts curated</th>'
            '<th data-i18n="th_voted">Voted</th><th data-i18n="th_rew">Rewards given</th></tr></thead><tbody>')
    return head + (out or '<tr><td colspan="5" data-i18n="lb_empty">No curators yet this month</td></tr>') + '</tbody></table>'

def attr(v): return html.escape(json.dumps(v, ensure_ascii=False), quote=True)

def inject(site, lb):
    page = os.path.join(site, "index.html")
    if not os.path.exists(page): return
    pp = '<a href="https://peakd.com/@pollenpatron" target="_blank" rel="noopener">@pollenpatron</a>'
    ym = lb.get("ym", "")
    sec = (f'{CSS}<section class="board" id="curators"><h2 data-i18n="lb_title" data-ym="{ym}" data-v="{attr({"month": lb["month"]})}">🏆 Wildflower Cup · {lb["month"]}</h2>'
           f'<p class="sub" data-i18n="lb_intro" data-v="{attr({"pp": pp, "n": lb["month_posts"]})}"></p>'
           f'<h3 data-i18n="lb_busy"></h3>{table(lb["contest"], True)}'
           f'<h3 style="margin-top:14px" data-i18n="lb_sweet"></h3>{table(lb.get("contest_rewards", []), True, True)}'
           f'<h2 style="margin-top:18px" data-i18n="lb_all"></h2>'
           f'<p class="sub" data-i18n="lb_all_sub" data-v="{attr({"n": lb["posts"], "r": format(lb["total_rewards"], ".2f")})}"></p>'
           f'{table(lb["curators"], False)}'
           f'<p class="note" data-i18n="lb_note"></p></section>\n')
    s = open(page, encoding="utf-8").read()
    s = s.replace("<footer>", sec + "<footer>", 1)
    s = s.replace('<span id="scan"></span></div>', '<span id="scan"></span><a href="#curators" style="color:var(--honey)" data-i18n="top_link">🏆 Wildflower Cup</a></div>', 1)
    # the page applies the translations once at start-up: run it again now that the board is in the page
    s = s.replace("</script></body>", "applyStatic();\n</script></body>", 1)
    open(page, "w", encoding="utf-8").write(s)

if __name__ == "__main__":
    os.makedirs(sys.argv[1], exist_ok=True)
    try: main(sys.argv[1])
    except Exception as e:                                         # the leaderboard must never break the page
        print("leaderboard skipped:", e, flush=True)
