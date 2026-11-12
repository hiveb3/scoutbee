# 🐝 Scout Bee · Wildflower Watch 🌼

**Open source Hive curation helper** by [@hive3](https://peakd.com/@hive3) · *The Hive Tree* 🌳

Every hour Scout Bee flies over the meadow and comes back with a dance: a list of **fresh, well-made Hive posts that are still waiting for their first visit**, so curators can find the small wildflowers that trending never shows.

🌼 **Live page: [hiveb3.github.io/scoutbee](https://hiveb3.github.io/scoutbee/)**, updated every hour (the time of the last update is shown at the top).

> 🧩 **Open source (MIT) and AI-generated.** This code was written with an AI (Claude, by Anthropic) and reviewed by a human. Idea by @antisocialist, data by @mahdiyari's [HAFSQL](https://hafsql.mahdiyari.info).

## 🌼 How a post is chosen

| Step | Rule |
|---|---|
| Fresh | top-level posts **1–15 hours old** |
| Waiting | pending rewards **at or below the median of the moment** |
| Well made | at least **300 words**, posted in a community, quality score ≥ 65: own photos, paragraphs, few external links, a **personal voice**; generic explainers, news-style articles, hashtag or all-caps titles are left out |
| Part of the hive | the author commented on other people's posts in the last week, reputation 30+ |
| Original | a sentence of each post is searched on the web (Brave Search API): text found elsewhere = left out |
| Safe | authors on the public on-chain blacklists/mute lists or muted in their community are skipped, plus anything downvoted by anti-abuse accounts, gray/hidden posts, declined payouts, NSFW |
| Fair | no flood posters (max 3 posts/24h), no copied text, one post per author, max 4 per community |
| New | posts already linked by **other newsletters or curation posts** are skipped |

AI-assisted posts are welcome like any other.

## 🐝 Curation trail

When a curator comments a post from the page with the **Wildflower Watch signature**, `follow_curators.py` makes **@scoutbee** and **@pollenpatron** vote the same post with the **same weight the curator used** (25% if the curator only commented; an account with under 500 HP always votes at 100%). Limits: max 10 votes a day per account, voting power above 80% (small votes of 25% or less still go out down to 50%), no votes to our own accounts, no self-curation. Every vote is public on chain.

## 🏆 Wildflower Cup (curation contest)

Every month the page shows **two cups**, each with its own podium: **🌼 most posts curated** (comments with the Wildflower Watch signature) and **🍯 most rewards given** with the curators' votes on those posts. The prize pool is **@pollenpatron**'s curation rewards of the month: half for each cup, split 60% / 25% / 15% among its top 3, paid liquid or in HP. Each cup closes at the end of the month and the winners are announced in a post in the first days of the next month. Our own accounts (🐝 @hive3 team) stay in the ranking but can't win. An all-time leaderboard (since November 2026) is shown below.

## 📦 Files

| File | Role |
|---|---|
| `scout.py` | finds and scores the posts (HAFSQL + a few `bridge` calls) → `candidates.json` |
| `build_site.py` | builds the web page from `candidates.json` |
| `i18n/*.json` | the page in 12 languages (EN, ES, PT, IT, DE, FR, PL, NL, UK, JA, ZH, HI), chosen from @enrique89's ranking of Hive users by country and posts by language; the reader picks one with the 🌐 menu |
| `leaderboard.py` | 🏆 Wildflower Cup: monthly and all-time curators leaderboard on the page (posts curated, rewards given with their votes) |
| `follow_curators.py` | curation trail: @scoutbee and @pollenpatron follow the curators' votes (runs on our server, keys never in the repo) |
| `.github/workflows/wildflower-watch.yml` | runs both every hour on GitHub Actions and publishes the page on GitHub Pages |

## 🛠️ Run your own copy

1. Fork this repository.
2. *Settings → Pages → Source*: **GitHub Actions**.
3. Optional: *Settings → Secrets and variables → Actions*: add `BRAVE_API_KEY` for the originality check (without it, the check is skipped).
4. *Actions → Wildflower Watch → Run workflow*.

To run it by hand: `pip install psycopg2-binary && SCOUTBEE_SITE=1 python3 scout.py out/run && python3 build_site.py out/run site`.

## 📜 License

MIT, see `LICENSE`. Built with love 💛 for every small flower in the Hive. 🐝🌼
