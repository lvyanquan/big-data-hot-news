# Source Catalog Maintenance

The editable catalog is [`sources.json`](sources.json).

## Source fields

- `id`: stable lowercase identifier. Do not rename after reports or automation depend on it.
- `name`: human-readable source name.
- `kind`: `rss`, `atom`, `json_list`, or `linkedin_engineering`.
- `url`: collection endpoint.
- `homepage`: canonical human-facing page when different from `url`.
- `tier`: `T1` official first-party, `T1_5` official social/person channel, or `T2` media/individual.
- `owner_key`: independent participant identity. Give a project's blog, GitHub releases, and official social channel the same value.
- `participation`: `editorial` for sources that can originate a report; `signal` for supporting discussion/release noise.
- `topics`: short maintained topic list.
- `enabled`: whether the collector includes it by default.
- `notes`: collection or editorial caveats.
- `config`: optional parser-specific configuration.

## Add or update a source

1. Prefer an official RSS or Atom endpoint over HTML scraping.
2. Verify that it returns current articles, valid dates, canonical links, and useful titles.
3. Use `editorial` if the source may be the only place an important event appears. A `signal` source cannot substitute for a missing primary editorial source.
4. Set `owner_key` to merge the organization's channels. Use project-level identities for Apache projects when their own channels should count together.
5. Mark high-frequency release feeds as `signal` only when another editorial source reliably announces stable releases. Otherwise leave them `editorial` and suppress RC/beta noise during ranking.
6. Keep full-text redistribution and licensing questions outside this catalog; it is a discovery catalog, not a republication grant.

## Validation

Validate JSON and inspect the catalog:

```bash
python3 -m json.tool references/sources.json >/dev/null
python3 scripts/collect_feeds.py --list
```

Run a short collection window:

```bash
python3 scripts/collect_feeds.py \
  --from 2026-10-09 \
  --to 2026-10-15 \
  --source apache-flink \
  --source apache-paimon-releases
```

Then run the skill validator:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  ~/.codex/skills/big-data-hot-news
```

## Remove or disable

Prefer `"enabled": false` when a source is temporarily broken, noisy, stale, or under review. Remove it only when it is permanently irrelevant or replaced, and note the replacement in the commit or task summary.
