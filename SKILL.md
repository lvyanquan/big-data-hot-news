---
name: big-data-hot-news
description: Research, deduplicate, evaluate, and summarize current news about databases, OLAP, streaming, data lakes, lakehouses, warehouses, and data engineering from a maintained source catalog. Use for big-data news scans, daily or weekly hotspot reports, date-range reviews, source audits, and updates to the catalog; do not use for timeless database tutorials or ordinary implementation questions.
---

# Big Data Hot News

Produce an evidence-grounded big-data news report from the maintained source catalog.

## Required references

- Read [`references/editorial-rubric.md`](references/editorial-rubric.md) before ranking or calling an item a hotspot.
- Read [`references/sources.json`](references/sources.json) for the current source catalog. Treat it as the maintained source of truth.
- Read [`references/source-maintenance.md`](references/source-maintenance.md) only when adding, removing, or changing sources.

## Workflow

1. Resolve the requested date range and timezone. Default to the user's timezone; otherwise use `Asia/Singapore` (`UTC+8`). State when the ending day is incomplete.
2. Run the feed collector for discovery when local execution is available:

   ```bash
   python3 scripts/collect_feeds.py --from YYYY-MM-DD --to YYYY-MM-DD
   ```

   Use `--list` to inspect the catalog and `--source <id>` to narrow collection.
3. Browse the web for current work. Verify shortlisted claims on official project, vendor, foundation, release, or engineering pages. The collector finds candidates; it is not sufficient evidence for a final factual claim.
4. Normalize articles into events. Merge duplicate official blog, GitHub release, LinkedIn, media, and repost coverage of the same occurrence. Use `owner_key` in the catalog to avoid treating several channels from one organization as independent participants.
5. Separate:
   - **Editorial value:** whether the event is worth readers' attention.
   - **Discussion heat:** how many independent organizations or communities are covering the same event, with more weight on recent coverage.
6. Rank using the rubric. Prefer stable releases, security notices, concrete architecture changes, reproducible engineering results, open-format developments, compatibility changes, and measured production lessons.
7. Down-rank RC/beta/nightly churn, unmeasured customer stories, event promotion, rebranding, routine patches, duplicated announcements, and vendor benchmarks without independent confirmation.
8. Write in the user's requested format. A useful default includes:
   - scope and methodology note;
   - ranked events with exact dates;
   - concise summary and why each matters;
   - sources/citations;
   - cross-event trends;
   - a watchlist for meaningful but lower-confidence items.

## Accuracy and wording

- Never claim the ranking is an AIHOT-computed heat index unless it was actually calculated from an AIHOT database.
- Label vendor-authored benchmarks as vendor claims and describe important test boundaries.
- Distinguish a formal stable release from an RC, beta, preview, or roadmap.
- Prefer exact dates and concrete metrics. Do not infer production adoption, performance, causality, or generality beyond the source.
- When reliable sources disagree, report the disagreement rather than blending claims.
- Do not treat multiple channels with the same `owner_key` as independent corroboration.

## Updating sources

The catalog is intentionally editable. When the user requests source changes, follow
[`references/source-maintenance.md`](references/source-maintenance.md), update
[`references/sources.json`](references/sources.json), then validate the skill and collector.
