#!/usr/bin/env python3
# Open source (MIT) · AI-generated with Claude (Anthropic), reviewed by a human · https://github.com/hiveb3/scoutbee
# Scout Bee - Wildflower Watch: finds fresh, well-made Hive posts that are still waiting for their first visit.
# Usage: python3 scout.py OUTDIR [NUMBER]      -> OUTDIR/post.md, OUTDIR/meta.json, OUTDIR/candidates.json
#        python3 scout.py --schema             -> prints the HAFSQL columns used (first-run check)
import sys, os, re, json, hashlib, statistics, datetime as dt, collections as C, urllib.request, urllib.parse, time

# ------------------------------------------------------------------ settings
MIN_AGE_H, MAX_AGE_H = 1, 15          # post age window (hours)
MIN_WORDS            = 300            # shorter posts are skipped
MIN_SCORE            = 65             # quality score threshold (raised: too many posts that deserved 0 got in)
MAX_POSTS            = 12             # posts per report: fewer, better
MIN_REPUTATION       = 30             # brand-new spam accounts sit at 25
MIN_PERSONAL         = 0.8            # first-person words per 100: below this the post reads like news or a generic article
MIN_COMMENTS_7D      = 2              # comments the author left on OTHER people's posts in the last 7 days
MAX_PER_COMMUNITY    = 3
MAX_POSTS_PER_AUTHOR_24H = 3          # more than this = flood, author skipped
NEWSLETTER_LOOKBACK_H = 36            # a post linked by another post in this window counts as "already featured"
REPEAT_AUTHOR_DAYS   = 7              # the same author is shown at most once in this many days
BLACKLIST_OBSERVERS  = ["themarkymark", "hivewatchers", "spaminator"]   # on-chain blacklists/mutes read with bridge.get_follow_list
ABUSE_DOWNVOTERS     = {"hivewatchers", "spaminator", "themarkymark", "buildawhale", "hive.guard"}
NSFW_TAGS            = {"nsfw", "porn", "xxx", "onlyfans"}
STOCK_HOSTS          = ("unsplash", "pixabay", "pexels", "shutterstock", "freepik", "istockphoto", "gettyimages", "wikimedia")
# generic SEO / explainer titles: rarely personal, often AI-farmed
GENERIC_TITLE        = re.compile(r"^(when is|when are|why is|why are|why do|how to|how do|how does|is it|should you|can you)\b|\b(what is|what are|a beginner'?s guide|ultimate guide|complete guide|explained|why .{1,30} is trending|top \d+|\d+ (tips|ways|reasons)|how to (earn|make money))\b", re.I)
# first-person words in the main Hive languages: a personal voice is what Hive readers reward
FIRST_PERSON         = {"my", "me", "mine", "we", "our", "yo", "mi", "mis", "nosotros", "nuestro", "nuestra", "io", "mio", "mia", "miei",
                        "noi", "nostro", "eu", "meu", "minha", "nós", "ich", "mein", "meine", "wir", "je", "mon", "mes", "nous"}   # English "I" is counted apart, only as a capital letter
HIVE_FOCUSED         = {"hive-111111", "hive-139531", "hive-163399", "hive-133987", "hive-170283", "hive-167922"}
NODES = ["https://api.hive.blog", "https://api.deathwing.me", "https://api.openhive.network"]
STATE = "state/featured.json"
SITE = os.environ.get("SCOUTBEE_SITE") == "1"   # website mode: hourly list, no "featured this week" memory
if SITE: MAX_POSTS, MAX_PER_COMMUNITY = 30, 4
WEEK = os.environ.get("SCOUTBEE_WEEK") == "1"   # weekly Hive post: "best of the week", posts 1-6.75 days old, still pending
if WEEK: MIN_AGE_H, MAX_AGE_H, MAX_POSTS, REPEAT_AUTHOR_DAYS = 24, 162, 15, 28
CHECKED = "state/checked.json"            # anti-plagiarism results already known (post -> "" or copy URL)
BRAVE_KEY = os.environ.get("BRAVE_API_KEY", "")   # anti-plagiarism web search (optional: skipped if missing)
PLAGIARISM_PHRASES   = 2                # exact-phrase searches per finalist
MAX_SEARCHES         = 40               # per run: keeps us inside Brave's free monthly credit
if SITE: PLAGIARISM_PHRASES, MAX_SEARCHES = 1, 1   # hourly site: 1 search an hour = ~720 a month, inside the free credit
if WEEK: PLAGIARISM_PHRASES, MAX_SEARCHES = 1, 20  # weekly post: max 20 searches (~90 a month): site + weekly stay well inside the credit
HIVE_FRONTENDS       = ("peakd.com", "ecency.com", "hive.blog", "inleo.io", "leofinance.io", "hiveblog", "waivio.com", "liketu.com",
                        "hivesuite.app", "3speak.tv", "actifit.io", "dbuzz", "stemsocial.com", "hivebuzz.me", "hiveblocks.com", "hive.ausbit.dev")
OWN = {"scoutbee", "beecounter", "hive3", "hive3.guard", "pollenpatron"}   # never feature our own accounts

def rpc(method, params):
    for i in range(6):
        try:
            req = urllib.request.Request(NODES[i % len(NODES)], method="POST", headers={"Content-Type": "application/json", "User-Agent": "scoutbee/1.1 (+https://peakd.com/@hive3)"},
                  data=json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode())
            r = json.load(urllib.request.urlopen(req, timeout=20))
            if "result" in r: return r["result"]
        except Exception as e:
            print("rpc retry", method, e, flush=True)
        time.sleep(1)
    raise RuntimeError("rpc failed: " + method)

def db():
    import psycopg2
    con = psycopg2.connect(host="hafsql-sql.mahdiyari.info", port=5432, dbname="haf_block_log",
                           user="hafsql_public", password="hafsql_public", connect_timeout=30)
    con.set_session(readonly=True, autocommit=True)
    cur = con.cursor(); cur.execute("SET statement_timeout = '600s'"); cur.execute("SET TIME ZONE 'UTC'")
    return cur

if sys.argv[1:2] == ["--schema"]:
    cur = db()
    cur.execute("""SELECT column_name, data_type FROM information_schema.columns
                   WHERE table_schema='hafsql' AND table_name='comments' ORDER BY ordinal_position""")
    for c in cur.fetchall(): print(*c)
    sys.exit(0)

OUT = sys.argv[1]; NUM = sys.argv[2] if len(sys.argv) > 2 else ""
os.makedirs(OUT, exist_ok=True); os.makedirs("state", exist_ok=True)
NOW = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None, microsecond=0)

# ------------------------------------------------------------------ 1. posts from HAFSQL
cur = db()
T0 = NOW - dt.timedelta(hours=max(MAX_AGE_H, NEWSLETTER_LOOKBACK_H, 24))
cur.execute("""SELECT author, permlink, title, body, json_metadata, category, created, net_rshares, deleted
               FROM hafsql.comments WHERE parent_author='' AND created >= %s""", (T0,))
rows = cur.fetchall()
print(len(rows), "top-level posts in the last", int((NOW - T0).total_seconds() // 3600), "hours", flush=True)

def utc(t): return t.astimezone(dt.timezone.utc).replace(tzinfo=None) if t.tzinfo else t
posts = [dict(a=a, p=p, t=t or "", body=b or "", jm=jm, cat=cat, created=utc(cr), net=float(net or 0))
         for a, p, t, b, jm, cat, cr, net, deleted in rows if not deleted]

# ------------------------------------------------------------------ 2. pending payout estimate (linear in rshares)
rf = rpc("condenser_api.get_reward_fund", ["post"]); fp = rpc("condenser_api.get_current_median_history_price", [])
usd_per_rshare = float(rf["reward_balance"].split()[0]) / float(rf["recent_claims"]) * \
                 float(fp["base"].split()[0]) / float(fp["quote"].split()[0])
for x in posts: x["est"] = max(x["net"], 0) * usd_per_rshare
window = [x for x in posts if MIN_AGE_H <= (NOW - x["created"]).total_seconds() / 3600 <= MAX_AGE_H]
median = statistics.median([x["est"] for x in window]) if window else 0
print(len(window), "posts in the age window; median pending ≈ $%.3f" % median, flush=True)

# ------------------------------------------------------------------ 3. "already featured" by other newsletters / curation posts
linked = set()
for x in posts:
    if (NOW - x["created"]).total_seconds() / 3600 > NEWSLETTER_LOOKBACK_H: continue
    for a, p in re.findall(r"/@([a-z0-9.\-]{3,16})/([a-z0-9\-]+)", x["body"]):
        if a != x["a"]: linked.add((a, p))
print(len(linked), "posts already linked by other posts", flush=True)

# ------------------------------------------------------------------ 4. blacklists (on-chain)
black = set()
for obs in BLACKLIST_OBSERVERS:
    for kind in ("blacklisted", "muted"):
        start = None
        for _ in range(200):
            params = {"observer": obs, "follow_type": kind, "limit": 100}
            if start: params["start"] = start
            try: res = rpc("bridge.get_follow_list", params)
            except Exception: break
            if not res: break
            for r in res: black.add(r["name"])
            if len(res) < 100: break
            start = res[-1]["name"]
extra = "blacklist_extra.txt"          # optional: one account per line (e.g. exported from hivewatchers.io)
if os.path.exists(extra):
    black |= {l.strip().lstrip("@").lower() for l in open(extra) if l.strip() and not l.startswith("#")}
print(len(black), "blacklisted / muted accounts", flush=True)

# ------------------------------------------------------------------ 5. text analysis and quality score
def clean(body):
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", body)               # markdown images
    t = re.sub(r"<[^>]+>", " ", t)                                # html
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)                # links -> text
    t = re.sub(r"https?://\S+", " ", t)
    return re.sub(r"[#*_>`|~\-]+", " ", t)

def analyse(x):
    b = x["body"]; txt = clean(b); words = re.findall(r"[^\W\d_]{2,}", txt)
    nw = len(words)
    imgs = len(re.findall(r"!\[[^\]]*\]\(|<img\s|https?://\S+\.(?:jpe?g|png|gif|webp)", b, re.I))
    links = len(re.findall(r"https?://", b)) - imgs
    heads = len(re.findall(r"^\s{0,3}#{1,4}\s", b, re.M))
    paras = len([p for p in re.split(r"\n\s*\n", txt) if len(p.split()) >= 15])
    caps = sum(1 for w in words if len(w) > 3 and w.isupper()) / max(nw, 1)
    s = 0
    s += 35 if 500 <= nw <= 1500 else 30 if nw > 1500 else 20 if nw >= MIN_WORDS else 0
    s += 15 if imgs >= 1 else 0
    s += 10 if paras >= 4 else 5 if paras >= 2 else 0
    s += 5 if heads >= 1 else 0
    s += 15 if x["cat"].startswith("hive-") else 0
    s += 10 if links <= 3 else 5 if links <= 8 else -10
    s -= 15 if caps > 0.15 else 0
    t = x["t"]; letters = [c for c in t if c.isalpha()]
    spam_title = t.count("#") >= 2 or (len(letters) > 15 and sum(c.isupper() for c in letters) / len(letters) > .7)
    generic = bool(GENERIC_TITLE.search(t))
    fp = (sum(1 for w in words if w.lower() in FIRST_PERSON) + len(re.findall(r"\bI\b", txt))) / max(nw, 1) * 100      # first-person words per 100
    latin = sum(1 for w in words if re.fullmatch(r"[A-Za-zÀ-ÿ]+", w)) / max(nw, 1)
    impersonal = latin >= .5 and fp < MIN_PERSONAL
    if latin >= .5:   # only for languages we can read (Korean, Chinese, Russian... stay neutral)
        s += 15 if fp >= 1.5 else 5 if fp >= .5 else -20                             # impersonal explainers lose points
    s -= 20 if generic else 0
    hosts = re.findall(r"https?://([^/\s)\"']+)", b)
    stock = sum(1 for h in hosts if any(k in h.lower() for k in STOCK_HOSTS))
    s -= 10 if imgs and stock >= imgs else 0                                          # only stock photos, no own pictures
    try: jm = json.loads(x["jm"]) if isinstance(x["jm"], str) else (x["jm"] or {})
    except Exception: jm = {}
    tags = {t.lower() for t in (jm.get("tags") or []) if isinstance(t, str)} | {x["cat"]}
    x.update(nw=nw, imgs=imgs, links=links, tags=tags, score=s, fp=round(fp, 2), generic=generic, spam_title=spam_title, impersonal=impersonal,
             hash=hashlib.sha1(re.sub(r"\W+", "", txt.lower())[:2000].encode()).hexdigest())
    return x

for x in posts: analyse(x)
dup = C.Counter(x["hash"] for x in posts if x["nw"] >= 50)
per_author = C.Counter(x["a"] for x in posts if (NOW - x["created"]).total_seconds() <= 86400)

state = json.load(open(STATE)) if os.path.exists(STATE) else {"posts": [], "authors": {}}
seen_posts = set(state["posts"])
recent_authors = {a for a, d in state["authors"].items() if (NOW - dt.datetime.fromisoformat(d)).days < REPEAT_AUTHOR_DAYS}

# ------------------------------------------------------------------ 6. filters
why = C.Counter(); cand = []
for x in window:
    key = (x["a"], x["p"])
    if x["a"] in OWN:                     why["own account"] += 1; continue
    if x["est"] > median:                 why["above median"] += 1; continue
    if x["nw"] < MIN_WORDS:               why["too short"] += 1; continue
    if x["a"] in black:                   why["blacklisted"] += 1; continue
    if x["tags"] & NSFW_TAGS:             why["nsfw"] += 1; continue
    if per_author[x["a"]] > MAX_POSTS_PER_AUTHOR_24H: why["flood"] += 1; continue
    if dup[x["hash"]] > 1:                why["duplicate text"] += 1; continue
    if key in linked:                     why["already in a newsletter"] += 1; continue
    if not SITE and f"{x['a']}/{x['p']}" in seen_posts: why["already featured by scoutbee"] += 1; continue
    if not SITE and x["a"] in recent_authors: why["author featured recently"] += 1; continue
    if x["spam_title"]:                   why["hashtag/shouting title"] += 1; continue
    if x["generic"]:                      why["generic how-to / explainer title"] += 1; continue
    if not x["cat"].startswith("hive-"):  why["not in a community"] += 1; continue
    if x["impersonal"]:                   why["impersonal (news / generic article)"] += 1; continue
    if x["score"] < MIN_SCORE:            why["low score"] += 1; continue
    cand.append(x)

# ------------------------------------------------------------------ 6b. is the author part of the hive? (comments to others, last 7 days)
talk = C.Counter()
if cand:
    cur.execute("""SELECT author, COUNT(*) FROM hafsql.comments
                   WHERE author = ANY(%s) AND parent_author <> '' AND parent_author <> author AND created >= %s
                   GROUP BY author""", (list({x["a"] for x in cand}), NOW - dt.timedelta(days=7)))
    talk.update(dict(cur.fetchall()))
kept = []
for x in cand:
    x["talk"] = talk[x["a"]]
    if x["talk"] < MIN_COMMENTS_7D: why["never comments on others"] += 1; continue
    kept.append(x)
cand = kept
print("after HAFSQL filters:", len(cand), dict(why), flush=True)

# ------------------------------------------------------------------ 6c. anti-plagiarism: exact phrases searched on the web (Brave Search)
searches = 0
checked = json.load(open(CHECKED)) if os.path.exists(CHECKED) else {}
def phrases(body):
    t = "\n".join(l for l in body.splitlines() if not l.lstrip().startswith(">"))       # quotes are allowed
    t = clean(t)
    sents = [re.sub(r"\s+", " ", x).strip() for x in re.split(r"(?<=[.!?])\s+|\n+", t)]
    sents = [x for x in sents if 12 <= len(x.split()) <= 30 and '"' not in x]
    sents.sort(key=lambda x: -len(set(w.lower() for w in x.split() if len(w) > 6)))     # most distinctive first
    return [" ".join(x.split()[:20]) for x in sents[:PLAGIARISM_PHRASES]]
def copied_from(x):
    """returns a URL where the same text exists and is not the author's own post, or None"""
    global searches
    key = f"{x['a']}/{x['p']}"
    x["orig"] = "unchecked"
    found = checked[key] if key in checked else (_search(x) if BRAVE_KEY else False)
    if found is False: return None
    checked[key] = found
    if found.startswith("?"):                      # same author name elsewhere, but no proof it is really theirs
        x["orig"] = "suspect"; x["elsewhere"] = found[1:]; return None
    x["orig"] = "ok"
    return found or None
def _search(x):
    global searches
    for ph in phrases(x["body"]):
        if searches >= MAX_SEARCHES: return False      # not checked: try again next run
        searches += 1; time.sleep(1.1)                                                 # free plan: 1 request per second
        try:
            req = urllib.request.Request("https://api.search.brave.com/res/v1/web/search?" +
                  urllib.parse.urlencode({"q": f'"{ph}"', "count": 5}),
                  headers={"X-Subscription-Token": BRAVE_KEY, "Accept": "application/json", "User-Agent": "scoutbee/1.1"})
            res = json.load(urllib.request.urlopen(req, timeout=20)).get("web", {}).get("results", [])
        except Exception as e:
            print("brave error", e, flush=True); continue
        for r in res:
            u = r.get("url", "").lower()
            if any(h in u for h in HIVE_FRONTENDS):                   # on Hive: a copy only if ANOTHER author published it FIRST
                m = re.search(r"/@([a-z0-9.\-]{3,16})/([a-z0-9\-]+)", u)
                if not m or m.group(1) == x["a"]: continue
                try: other = rpc("bridge.get_post", {"author": m.group(1), "permlink": m.group(2)})
                except Exception: other = None
                if other and other.get("created") and dt.datetime.fromisoformat(other["created"][:19]) < x["created"]:
                    return r.get("url")
                continue                                            # newer: a curation post quoting this one
            # own cross-post only with a proof: (1) the Hive post links that site, or (3) the Hive post is older than the page
            dom = urllib.parse.urlparse(u).netloc.removeprefix("www.")
            if dom and dom in x["body"].lower(): continue
            try: page = dt.datetime.fromisoformat(str(r.get("page_age", ""))[:19])
            except ValueError: page = None
            if page and x["created"] < page: continue
            if re.sub(r"[^a-z0-9]", "", x["a"]) in re.sub(r"[^a-z0-9]", "", u): return "?" + r.get("url", "")   # same name, no proof: to be checked
            return r.get("url")
    return ""

# ------------------------------------------------------------------ 7. final check on the chain (only the finalists)
cand.sort(key=lambda x: (x["est"], -x["score"]))
final, comm = [], C.Counter()
mutes_cache = {}
def community_muted(c):
    if c not in mutes_cache:
        try: mutes_cache[c] = {r[0] for r in rpc("bridge.list_community_roles", {"community": c, "limit": 1000}) if r[1] == "muted"}
        except Exception: mutes_cache[c] = set()
    return mutes_cache[c]

for x in cand:
    if len(final) >= MAX_POSTS: break
    if any(f["a"] == x["a"] for f in final): continue
    if comm[x["cat"]] >= MAX_PER_COMMUNITY: continue
    try: p = rpc("bridge.get_post", {"author": x["a"], "permlink": x["p"]})
    except Exception: continue
    if not p or p.get("stats", {}).get("gray") or p.get("stats", {}).get("hide"): why["gray/hidden"] += 1; continue
    if float(str(p.get("max_accepted_payout", "1")).split()[0]) == 0: why["payout declined"] += 1; continue
    if p.get("author_reputation", 25) < MIN_REPUTATION: why["low reputation"] += 1; continue
    if any(int(v.get("rshares", 0)) < 0 and v["voter"] in ABUSE_DOWNVOTERS for v in p.get("active_votes", [])):
        why["anti-abuse downvote"] += 1; continue
    if x["cat"].startswith("hive-") and x["a"] in community_muted(x["cat"]): why["muted in community"] += 1; continue
    src = copied_from(x)
    if WEEK and x["orig"] == "suspect": why["text also elsewhere (to check)"] += 1; print("  check?", x["a"], x["p"], "->", x["elsewhere"], flush=True); continue
    if src: why["possible copy (web)"] += 1; print("  copy?", x["a"], x["p"], "->", src, flush=True); continue
    x["pending"] = float(str(p.get("pending_payout_value", "0")).split()[0])
    x["ctitle"] = p.get("community_title") or x["cat"]
    x["votes"] = len([v for v in p.get("active_votes", []) if int(v.get("rshares", 0)) > 0])
    final.append(x); comm[x["cat"]] += 1

# hive-focused first if the list is long
if len(cand) > MAX_POSTS * 2:
    final.sort(key=lambda x: (x["cat"] not in HIVE_FOCUSED, x["pending"], -x["score"]))
else:
    final.sort(key=lambda x: (x["pending"], -x["score"]))
json.dump({k: v for k, v in list(checked.items())[-3000:]}, open(CHECKED, "w"))
print("final:", len(final), dict(why), "· web searches:", searches if BRAVE_KEY else "off (no BRAVE_API_KEY)", flush=True)

# ------------------------------------------------------------------ 7b. weekly: new witness voters of hive3 (to thank them)
new_witness_voters = []
if WEEK:
    try:
        head = rpc("condenser_api.get_dynamic_global_properties", [])["head_block_number"]
        since = (head - 7 * 24 * 1200) << 32              # HAF operation id = block number << 32: one block every 3 seconds
        cur.execute("""SELECT account, approve FROM hafsql.operation_account_witness_vote_table
                       WHERE witness = 'hive3' AND id >= %s ORDER BY id""", (since,))
        last = {}
        for acc, approve in cur.fetchall(): last[acc] = approve           # the last action of the week counts
        new_witness_voters = sorted(a for a, ok in last.items() if ok and a not in OWN)
        print(len(new_witness_voters), "new witness voters this week", flush=True)
    except Exception as e:
        print("witness voters: query failed", e, flush=True)

# ------------------------------------------------------------------ 8. post (authors linked, never @-tagged)
def link_author(a): return f"[{a}](/@{a})"
def esc(t): return re.sub(r"[\[\]|]", " ", t).replace("@", "").strip()[:90] or "(untitled)"
day = NOW.strftime("%B %-d, %Y")
L = []
L.append("<center>\n\nIMG:cover.png\n\n</center>\n" if os.path.exists(os.path.join(OUT, "cover.png")) else "")
L.append(("Bzzz! 🐝💃 Hello, hive! Here is the **best of the week** from the meadow: "
          f"**{len(final)} well-made posts** of the last 7 days that are still **under-rewarded**, and still have time to be voted before payout. 🌼\n"
          "Every hour the full, fresh list lives at **[hiveb3.github.io/scoutbee](https://hiveb3.github.io/scoutbee/)**. 🐝\n") if WEEK else
         ("Bzzz! 🐝💃 Hello, hive! Your little scout bee just came back from the meadow, and here is today's dance: "
          f"**{len(final)} fresh posts**, published in the last {MAX_AGE_H} hours, that are well made and still waiting for their first visit. 🌼\n"))
L.append("They are sorted from the **least rewarded** up. A vote, a comment, or even just a read can make someone's day. 🍯\n\n---\n")
for i, x in enumerate(final, 1):
    age = (NOW - x["created"]).total_seconds() / 3600
    L.append(f"**{i}. [{esc(x['t'])}](/{x['cat']}/@{x['a']}/{x['p']})**  \n"
             f"🌱 by {link_author(x['a'])} · in *{esc(x['ctitle'])}* · {x['nw']:,} words · "
             f"{'📷 ' if x['imgs'] else ''}{(f'{age / 24:.0f} days' if age >= 48 else f'{age:.0f}h')} old · pending ${x['pending']:.2f} · {x['votes']} vote{'s' if x['votes'] != 1 else ''}\n")
if WEEK and new_witness_voters:
    L.append("\n---\n\n### 🗳️ Thank you, new witness voters!\n")
    L.append("This week " + ", ".join(link_author(a) for a in new_witness_voters) +
             f" started voting [hive3 as witness](https://vote.hive.uno/@hive3). Thank you: your vote keeps a little node, and this little bee, flying. 💛🐝\n")
L.append("\n---\n\n### 🐝 How the scout bee chooses\n")
L.append((f"- Top-level posts **1 to 7 days old**, still before payout, with pending rewards **at or below the median** (≈ ${median:.2f}).\n" if WEEK else
          f"- Top-level posts **{MIN_AGE_H}–{MAX_AGE_H} hours old**, with pending rewards **at or below today's median** (≈ ${median:.2f}).\n") +
         f"- At least **{MIN_WORDS} words**, plus a quality score: length, own photos, paragraphs, community, few external links, a **personal voice**; generic \"what is / how to / beginner's guide\" explainers, news-style articles with no personal voice, and hashtag or all-caps titles are left out.\n"
         f"- Posted **in a community**, and the author must be **part of the hive**: at least {MIN_COMMENTS_7D} comments on other people's posts in the last week, and a reputation of {MIN_REPUTATION}+.\n"
         "- **Anti-plagiarism:** a few exact sentences of each post are searched on the web; posts whose text already exists elsewhere are left out.\n"
         "- **Skipped:** authors on the public blacklists or muted in their community, flood posting, copied text, NSFW, declined payouts, "
         f"posts already linked by other newsletters or curation posts, and authors featured in the last {REPEAT_AUTHOR_DAYS} days.\n"
         f"- One post per author, max {MAX_PER_COMMUNITY} per community. Authors are **linked, not tagged**, so nobody gets a notification from a bot.\n"
         "- AI-assisted posts are welcome, like any other.\n")
L.append("\n<sub>🔥 100% of this post's rewards are **burned** (beneficiary null). Scout Bee is an open source, AI-generated bot operated by "
         "[hive3](/@hive3): code at [github.com/hiveb3/scoutbee](https://github.com/hiveb3/scoutbee). Spotted a post that shouldn't be here, "
         "or a hidden gem we missed? Tell us in the comments. 🌼</sub>\n")
open(os.path.join(OUT, "post.md"), "w", encoding="utf-8").write("\n".join(L))

title = (f"🌼 Wildflower Watch · Best of the week{(' #' + NUM) if NUM else ''}: {len(final)} under-rewarded gems ({day})" if WEEK else
         f"🌼 Wildflower Watch{(' #' + NUM) if NUM else ''}: {len(final)} fresh posts still waiting for their first visit ({day})")
meta = dict(title=title, permlink=(f"wildflower-watch-week-{NOW.strftime('%Y-%m-%d')}" if WEEK else f"wildflower-watch-{NOW.strftime('%Y-%m-%d')}"),
            description=(f"The best of the week: {len(final)} well-made Hive posts still under-rewarded, before payout. By a scout bee 🐝🌼" if WEEK else
                         f"{len(final)} fresh, well-made Hive posts still waiting for their first visit. Curated daily by a scout bee 🐝🌼"),
            tags=["hive-170283", "curation", "hive", "newbies", "wildflowerwatch", "discovery", "aibees"],
            images=["cover.png"] if os.path.exists(os.path.join(OUT, "cover.png")) else [], community="hive-170283")
json.dump(meta, open(os.path.join(OUT, "meta.json"), "w"), ensure_ascii=False, indent=1)
json.dump([{k: v for k, v in x.items() if k not in ("body", "jm", "tags", "hash", "elsewhere")} | {"created": x["created"].isoformat(), "tags": sorted(x["tags"])[:8]}
           for x in final], open(os.path.join(OUT, "candidates.json"), "w"), ensure_ascii=False, indent=1)
json.dump(dict(why=why, median=median, window=len(window), generated=NOW.isoformat() + "Z", searches=searches), open(os.path.join(OUT, "stats.json"), "w"), indent=1)
print("OK", OUT, title)
