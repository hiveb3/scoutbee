#!/usr/bin/env python3
# Open source (MIT) · AI-generated with Claude (Anthropic), reviewed by a human · https://github.com/hiveb3/scoutbee
# Scout Bee - curation trail: when a curator signs a post with the Wildflower Watch signature,
# @scoutbee and @pollenpatron vote the same post with the same weight the curator used
# (a voter with little HP always votes at 100%).
#
# Usage:  python3 follow_curators.py            -> votes for real (keys from the environment)
#         python3 follow_curators.py --dry-run  -> only prints what it would do
# Keys:   SCOUTBEE_POSTING_KEY, POLLENPATRON_POSTING_KEY (posting keys only, never in the repo)
# Needs:  pip install psycopg2-binary lighthive
import os, sys, json, time, datetime as dt, urllib.request

VOTERS = {   # account -> environment variable with its posting key
    "scoutbee": "SCOUTBEE_POSTING_KEY",
    "pollenpatron": "POLLENPATRON_POSTING_KEY",
}
LOOKBACK_H      = 24        # signed comments of the last N hours
DEFAULT_WEIGHT  = 25        # % used when the curator signed but did not vote (or voted 0)
MAX_WEIGHT      = 100       # never above this %
MIN_VP          = 80        # % voting power: below this the account waits (keeps its strength)
MAX_VOTES_DAY   = 10        # per voter, every 24 hours
LOW_HP          = 500       # a voter with less HP than this always votes at 100% (its vote is tiny anyway)
MAX_POST_AGE_D  = 6.5       # posts older than this can't earn rewards anymore
SKIP_AUTHORS    = set(VOTERS) | {"hive3"}   # no self-votes and no votes to our own accounts
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state", "trail.json")
NODES = ["https://api.hive.blog", "https://api.deathwing.me", "https://api.openhive.network"]
DRY = "--dry-run" in sys.argv

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

def signed_comments():
    """Comments carrying the Wildflower Watch signature (made from the site) in the last LOOKBACK_H hours."""
    import psycopg2
    con = psycopg2.connect(host="hafsql-sql.mahdiyari.info", port=5432, dbname="haf_block_log",
                           user="hafsql_public", password="hafsql_public", connect_timeout=30)
    cur = con.cursor()
    since = dt.datetime.utcnow() - dt.timedelta(hours=LOOKBACK_H)
    cur.execute("""SELECT author, parent_author, parent_permlink, created FROM hafsql.comments
                   WHERE parent_author <> '' AND created >= %s
                     AND (body LIKE '%%hiveb3.github.io/scoutbee%%' OR json_metadata::text LIKE '%%wildflowerwatch%%')""", (since,))
    rows = cur.fetchall(); con.close()
    return [(a, pa, pp) for a, pa, pp, _ in rows]

def voting_power(acc):
    a = rpc("condenser_api.get_accounts", [[acc]])[0]
    vp = a["voting_manabar"]["current_mana"]
    eff = float(a["vesting_shares"].split()[0]) + float(a["received_vesting_shares"].split()[0]) - float(a["delegated_vesting_shares"].split()[0])
    mx = eff * 1e6
    if mx <= 0: return 100.0, 0.0          # no HP yet: the vote is free (and worth ~0)
    last = a["voting_manabar"]["last_update_time"]
    vp = min(mx, vp + mx * (time.time() - last) / 432000)
    return 100 * vp / mx, eff

def hp_per_vest():
    g = rpc("condenser_api.get_dynamic_global_properties", [])
    return float(g["total_vesting_fund_hive"].split()[0]) / float(g["total_vesting_shares"].split()[0])

def load():
    try: return json.load(open(STATE))
    except Exception: return {"done": [], "log": {}}

def save(s):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    s["done"] = s["done"][-2000:]
    json.dump(s, open(STATE, "w"), indent=1)

def main():
    st = load(); now = time.time()
    for v in VOTERS: st["log"][v] = [t for t in st["log"].get(v, []) if now - t < 86400]
    jobs = {}
    for curator, a, p in signed_comments():
        if a in SKIP_AUTHORS or a == curator: continue           # no votes to our accounts, no self-curation
        jobs.setdefault((a, p), set()).add(curator)
    print(f"signed posts: {len(jobs)}", flush=True)
    clients = {}
    HPV = hp_per_vest()
    for (a, p), curators in jobs.items():
        post = rpc("condenser_api.get_content", [a, p])
        if not post.get("author") or post.get("parent_author"): continue          # deleted or not a top-level post
        age_d = (dt.datetime.utcnow() - dt.datetime.fromisoformat(post["created"])).total_seconds() / 86400
        if age_d > MAX_POST_AGE_D or post.get("max_accepted_payout", "1").startswith("0.000"): continue
        votes = {x["voter"]: x for x in rpc("condenser_api.get_active_votes", [a, p])}
        cw = [votes[c]["percent"] / 100 for c in curators if c in votes and votes[c]["percent"] > 0 and c not in VOTERS]
        weight = min(MAX_WEIGHT, max(cw) if cw else DEFAULT_WEIGHT)
        for v, envk in VOTERS.items():
            key = f"{v}/{a}/{p}"
            if key in st["done"] or v in votes or curators == {v}: continue   # a voter does not follow itself
            if len(st["log"][v]) >= MAX_VOTES_DAY: print(f"{v}: daily limit reached", flush=True); continue
            vp, eff = voting_power(v)
            hp = eff * HPV
            w = 100 if hp < LOW_HP else weight                       # little HP: always a full vote
            if hp >= LOW_HP and vp < MIN_VP: print(f"{v}: VP {vp:.1f}% < {MIN_VP}%, waiting", flush=True); continue
            print(f"{'[dry] ' if DRY else ''}{v} votes @{a}/{p} at {w:.0f}% (curated by {', '.join(sorted(curators))}, {hp:.0f} HP, VP {vp:.1f}%)", flush=True)
            if DRY: continue
            if not os.environ.get(envk): print(f"{v}: missing {envk}, skipped", flush=True); continue
            if v not in clients:
                from lighthive.client import Client
                clients[v] = Client(keys=[os.environ[envk]], nodes=NODES)
            from lighthive.datastructures import Operation
            try:
                clients[v].broadcast(Operation("vote", {"voter": v, "author": a, "permlink": p, "weight": int(w * 100)}))
                st["done"].append(key); st["log"][v].append(now); time.sleep(4)
            except Exception as e:
                print(f"{v}: vote failed on @{a}/{p}: {e}", flush=True)
    if not DRY: save(st)

if __name__ == "__main__":
    main()
