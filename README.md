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

## 📦 Files

| File | Role |
|---|---|
| `scout.py` | finds and scores the posts (HAFSQL + a few `bridge` calls) → `candidates.json` |
| `build_site.py` | builds the web page from `candidates.json` |
| `.github/workflows/wildflower-watch.yml` | runs both every hour on GitHub Actions and publishes the page on GitHub Pages |

## 🛠️ Run your own copy

1. Fork this repository.
2. *Settings → Pages → Source*: **GitHub Actions**.
3. Optional: *Settings → Secrets and variables → Actions*: add `BRAVE_API_KEY` for the originality check (without it, the check is skipped).
4. *Actions → Wildflower Watch → Run workflow*.

To run it by hand: `pip install psycopg2-binary && SCOUTBEE_SITE=1 python3 scout.py out/run && python3 build_site.py out/run site`.

## 📜 License

MIT, see `LICENSE`. Built with love 💛 for every small flower in the Hive. 🐝🌼
