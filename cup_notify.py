#!/usr/bin/env python3
# Open source (MIT) · AI-generated with Claude (Anthropic), reviewed by a human · https://github.com/hiveb3/scoutbee
# Scout Bee - Wildflower Cup news: when a curator's position in the TOP 5 of the monthly Cup changes
# (enters the top 5, climbs, or slips down), @scoutbee leaves a friendly comment on the curator's latest post,
# like @hivebuzz does for badges, inviting them to keep playing with Wildflower Watch.
#
# Usage:  python3 cup_notify.py            -> sends the comments (key from the environment)
#         python3 cup_notify.py --dry-run  -> only prints what it would send
# Key:    POSTING_KEY_SCOUTBEE (or SCOUTBEE_POSTING_KEY), posting key only, never in the repo
# Needs:  pip install lighthive
# The first run only remembers the current ranking (no comments), so nobody gets a message for the past.
import os, sys, json, time, datetime as dt, urllib.request

SITE = "https://hiveb3.github.io/scoutbee/leaderboard.json"
# The link in the comment uses "HiveB3" with capitals on purpose: it opens the same page, but it does NOT
# match the Wildflower Watch signature (hiveb3.github.io/scoutbee), so these news comments are never counted
# as curation and the trail never votes because of them.
PAGE = "https://HiveB3.github.io/scoutbee/#curators"
TOP = 5
BOARDS = {"contest": "most posts curated", "contest_rewards": "most rewards given"}
TEAM_SKIP = True               # our own accounts (marked "team") get no messages
MIN_GAP_H = 24                 # at most one message per curator every 24 hours
MAX_POST_AGE_D = 6.5           # comment on the latest post only if it is still open (not paid out)
ACCOUNT = "scoutbee"
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state", "cup.json")
NODES = ["https://api.hive.blog", "https://api.deathwing.me", "https://api.openhive.network"]
DRY = "--dry-run" in sys.argv
MEDAL = {1: "🥇", 2: "🥈", 3: "🥉", 4: "4️⃣", 5: "5️⃣"}

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

def ranks(lb, board):
    out, n = {}, 0
    for c in lb.get(board, []):
        if TEAM_SKIP and c.get("team"): continue
        if board == "contest_rewards" and not c.get("rewards"): continue
        n += 1
        if n > TOP: break
        out[c["curator"]] = (n, c)
    return out

def message(who, board, old, new, c, month):
    what = BOARDS[board]
    if old is None:   head = f"Bzzz! 🐝🌼 Big news from the Wildflower Cup, @{who}: you just flew **into the top {TOP}** for *{what}*, at place **{MEDAL[new]} {new}**!"
    elif new < old:   head = f"Bzzz! 🐝🌼 You're climbing, @{who}! In the Wildflower Cup for *{what}* you moved **up from {old} to {MEDAL[new]} {new}**!"
    else:             head = f"Bzzz! 🐝🌼 Heads up, @{who}: in the Wildflower Cup for *{what}* another bee passed you, and you're now **{MEDAL[new]} {new}** (you were {old})."
    stats = f"So far in {month}: **{c['posts']}** flowers curated, **${c['rewards']:.2f}** of rewards given with your votes."
    cheer = ("Keep visiting the flowers nobody has seen yet: every vote and every kind word can make someone's day, "
             "and the top 3 at the end of the month share the prize! 🍯" if new > 1 else
             "You're leading the swarm! Keep the honey flowing, the other bees are buzzing right behind you. 🍯")
    return (f"{head}\n\n{stats}\n\n{cheer}\n\n🌼 Play again on **[Wildflower Watch]({PAGE})** "
            f"and see the whole Cup.\n\n<sub>🤖 Automated news from @scoutbee, a bot of the @hive3 hive · "
            f"we write at most once a day, only when your top-{TOP} place changes.</sub>")

def latest_post(acc):
    for p in rpc("bridge.get_account_posts", {"sort": "posts", "account": acc, "limit": 3}) or []:
        age = (dt.datetime.utcnow() - dt.datetime.fromisoformat(p["created"])).total_seconds() / 86400
        if age <= MAX_POST_AGE_D: return p
    return None

def main():
    lb = json.load(urllib.request.urlopen(SITE + "?t=" + str(int(time.time())), timeout=30))
    month = lb.get("ym", "")
    try: st = json.load(open(STATE))
    except Exception: st = {}
    first = st.get("month") != month                    # new month (or first run): just remember the ranking
    now = time.time(); sent = st.get("sent", {})
    news = {}
    for board in BOARDS:
        cur, prev = ranks(lb, board), st.get("ranks", {}).get(board, {})
        for who, (n, c) in cur.items():
            old = prev.get(who)
            if old != n and not first:
                news.setdefault(who, (board, old, n, c))     # one message per curator: the first board that changed
    client = None
    for who, (board, old, n, c) in news.items():
        if now - sent.get(who, 0) < MIN_GAP_H * 3600: print(f"@{who}: messaged less than {MIN_GAP_H}h ago, skipped"); continue
        p = latest_post(who)
        if not p: print(f"@{who}: no open post to comment on, skipped"); continue
        body = message(who, board, old, n, c, lb.get("month", month))
        print(f"{'[dry] ' if DRY else ''}@{who} {board}: {old} -> {n} · on /@{who}/{p['permlink']}\n{body}\n", flush=True)
        if DRY: continue
        key = os.environ.get("POSTING_KEY_SCOUTBEE") or os.environ.get("SCOUTBEE_POSTING_KEY")
        if not key: print("no posting key for @scoutbee: nothing sent"); break
        if client is None:
            from lighthive.client import Client
            client = Client(keys=[key], nodes=NODES)
        from lighthive.datastructures import Operation
        perm = f"re-{who}-wildflowercup-{int(now)}".lower().replace(".", "-")[:255]
        try:
            client.broadcast(Operation("comment", {"parent_author": who, "parent_permlink": p["permlink"], "author": ACCOUNT,
                "permlink": perm, "title": "", "body": body, "json_metadata": json.dumps({"app": "scoutbee-cup/1.0", "tags": ["wildflowercup"]})}))
            sent[who] = now; time.sleep(4)
        except Exception as e:
            print(f"@{who}: comment failed: {e}", flush=True)
    if not DRY:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        json.dump({"month": month, "ranks": {b: {w: n for w, (n, c) in ranks(lb, b).items()} for b in BOARDS},
                   "sent": {k: v for k, v in sent.items() if now - v < 7 * 86400}}, open(STATE, "w"), indent=1)
    print("cup_notify: done", "(first run of the month: ranking saved, no messages)" if first else "", flush=True)

if __name__ == "__main__":
    main()
