#!/usr/bin/env python3
"""Collect date-bounded candidates from the big-data source catalog.

This is a discovery helper. Final reports must verify shortlisted claims on the
canonical official pages and apply the editorial rubric.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, time, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import time as sleep_time
from typing import Any
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
import xml.etree.ElementTree as ET


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = SKILL_DIR / "references" / "sources.json"
USER_AGENT = "Mozilla/5.0 Codex big-data-hot-news collector"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def clean_text(value: str) -> str:
    value = re.sub(r"<(script|style)\b[^>]*>[\s\S]*?</\1>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", unescape(value)).strip()


def element_text(element: ET.Element, names: tuple[str, ...]) -> str:
    for child in list(element):
        if local_name(child.tag) in names:
            return unescape(" ".join("".join(child.itertext()).split())).strip()
    return ""


def element_link(element: ET.Element, base_url: str) -> str:
    for child in list(element):
        if local_name(child.tag) != "link":
            continue
        text = " ".join("".join(child.itertext()).split()).strip()
        if text:
            return urljoin(base_url, text)
        href = child.attrib.get("href", "")
        rel = child.attrib.get("rel", "alternate")
        if href and rel in ("", "alternate"):
            return urljoin(base_url, href)
    return ""


def parse_datetime(value: str, default_tz: ZoneInfo) -> datetime | None:
    value = value.strip()
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=default_tz)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        pass
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=default_tz)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        pass
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=default_tz).astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def fetch(url: str, attempts: int = 4, timeout: int = 40) -> tuple[bytes, str]:
    error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
            with urlopen(request, timeout=timeout) as response:
                return response.read(12_000_000), response.geturl()
        except Exception as exc:  # network failures differ across platforms
            error = exc
            if attempt + 1 < attempts:
                sleep_time.sleep(1 + attempt * 2)
    assert error is not None
    raise error


def collect_feed(source: dict[str, Any], source_tz: ZoneInfo) -> list[dict[str, Any]]:
    data, final_url = fetch(source["url"])
    root = ET.fromstring(data)
    results: list[dict[str, Any]] = []
    for entry in root.iter():
        if local_name(entry.tag) not in ("item", "entry"):
            continue
        title = element_text(entry, ("title",))
        link = element_link(entry, final_url)
        raw_date = element_text(entry, ("pubDate", "published", "updated", "date"))
        published = parse_datetime(raw_date, source_tz)
        summary = element_text(entry, ("description", "summary", "content", "encoded"))
        categories = [
            unescape(" ".join("".join(child.itertext()).split())).strip()
            for child in list(entry)
            if local_name(child.tag) == "category"
        ]
        if title and link:
            results.append(
                {
                    "title": title,
                    "url": link,
                    "published_at": published,
                    "date_raw": raw_date,
                    "summary": clean_text(summary)[:1200],
                    "categories": [category for category in categories if category],
                }
            )
    return results


def path_value(value: Any, path: str) -> Any:
    if path == "":
        return value
    current = value
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def collect_json_list(source: dict[str, Any], source_tz: ZoneInfo) -> list[dict[str, Any]]:
    data, _final_url = fetch(source["url"])
    document = json.loads(data)
    config = source.get("config", {})
    items = path_value(document, config.get("items_path", ""))
    if not isinstance(items, list):
        raise ValueError("items_path did not resolve to a list")
    results: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = path_value(item, config["title_path"])
        raw_date = path_value(item, config["date_path"])
        external_id = path_value(item, config.get("id_path", "id"))
        summary = path_value(item, config.get("summary_path", ""))
        template = config["url_template"]
        link = template.replace("{id}", str(external_id))
        if isinstance(title, str) and title.strip() and external_id is not None:
            results.append(
                {
                    "title": title.strip(),
                    "url": link,
                    "published_at": parse_datetime(str(raw_date or ""), source_tz),
                    "date_raw": str(raw_date or ""),
                    "summary": clean_text(str(summary or ""))[:1200],
                    "categories": list(item.get("categories", [])) if isinstance(item.get("categories"), list) else [],
                }
            )
    return results


class LinkedInEngineeringParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.results: list[dict[str, str]] = []
        self.current: dict[str, str] | None = None
        self.item_depth = 0
        self.capture: str | None = None
        self.capture_tag: str | None = None
        self.parts: list[str] = []

    @staticmethod
    def classes(attrs: list[tuple[str, str | None]]) -> set[str]:
        value = dict(attrs).get("class") or ""
        return set(value.split())

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = self.classes(attrs)
        values = dict(attrs)
        if tag == "li" and {"post-list__item", "grid-post"}.issubset(classes):
            if self.current is None:
                self.current = {}
                self.item_depth = 1
            else:
                self.item_depth += 1
            return
        if self.current is not None and tag == "li":
            self.item_depth += 1
        if self.current is None:
            return
        if tag == "a" and "grid-post__link" in classes:
            self.current["url"] = urljoin(self.base_url, values.get("href") or "")
            self.capture, self.capture_tag, self.parts = "title", "a", []
        elif tag == "p" and "grid-post__date" in classes:
            self.capture, self.capture_tag, self.parts = "date", "p", []
        elif tag == "p" and "grid-post__author" in classes:
            self.capture, self.capture_tag, self.parts = "author", "p", []

    def handle_data(self, data: str) -> None:
        if self.capture:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self.capture and tag == self.capture_tag and self.current is not None:
            self.current[self.capture] = " ".join("".join(self.parts).split())
            self.capture = self.capture_tag = None
            self.parts = []
        if self.current is not None and tag == "li":
            self.item_depth -= 1
            if self.item_depth == 0:
                if self.current.get("title") and self.current.get("url"):
                    self.results.append(self.current)
                self.current = None


def collect_linkedin_engineering(source: dict[str, Any], source_tz: ZoneInfo) -> list[dict[str, Any]]:
    data, final_url = fetch(source["url"])
    parser = LinkedInEngineeringParser(final_url)
    parser.feed(data.decode("utf-8", "ignore"))
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for item in parser.results:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        results.append(
            {
                "title": item["title"],
                "url": item["url"],
                "published_at": parse_datetime(item.get("date", ""), source_tz),
                "date_raw": item.get("date", ""),
                "summary": "",
                "categories": [],
                "author": item.get("author", ""),
            }
        )
    return results


def collect_source(source: dict[str, Any], source_tz: ZoneInfo) -> list[dict[str, Any]]:
    kind = source["kind"]
    if kind in ("rss", "atom"):
        return collect_feed(source, source_tz)
    if kind == "json_list":
        return collect_json_list(source, source_tz)
    if kind == "linkedin_engineering":
        return collect_linkedin_engineering(source, source_tz)
    raise ValueError(f"unsupported source kind: {kind}")


def load_catalog(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        value = json.load(file)
    if not isinstance(value.get("sources"), list):
        raise ValueError("catalog must contain a sources list")
    return value


def parse_day(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected YYYY-MM-DD") from exc


def render_table(rows: list[dict[str, Any]]) -> str:
    lines = ["DATE       SOURCE                         TITLE", "-" * 100]
    for row in rows:
        lines.append(f"{row['local_date']:<10} {row['source_name'][:28]:<30} {row['title']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--from", dest="from_day", type=parse_day)
    parser.add_argument("--to", dest="to_day", type=parse_day)
    parser.add_argument("--timezone")
    parser.add_argument("--source", action="append", default=[], help="source id; may be repeated")
    parser.add_argument("--include-disabled", action="store_true")
    parser.add_argument("--list", action="store_true", help="list catalog sources and exit")
    parser.add_argument("--format", choices=("jsonl", "json", "table"), default="jsonl")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--concurrency", type=int, default=8)
    args = parser.parse_args()

    catalog = load_catalog(args.catalog)
    sources: list[dict[str, Any]] = catalog["sources"]
    if args.list:
        for source in sources:
            state = "on " if source.get("enabled", True) else "off"
            print(
                f"{state}  {source['id']:<28} {source['kind']:<20} "
                f"{source['tier']:<4} {source['participation']:<9} {source['name']}"
            )
        return 0

    if args.from_day is None or args.to_day is None:
        parser.error("--from and --to are required unless --list is used")
    if args.to_day < args.from_day:
        parser.error("--to must be on or after --from")

    timezone_name = args.timezone or catalog.get("default_timezone", "Asia/Singapore")
    local_tz = ZoneInfo(timezone_name)
    start = datetime.combine(args.from_day, time.min, tzinfo=local_tz).astimezone(timezone.utc)
    end = datetime.combine(args.to_day + timedelta(days=1), time.min, tzinfo=local_tz).astimezone(timezone.utc)

    selected_ids = set(args.source)
    chosen = [
        source
        for source in sources
        if (not selected_ids or source["id"] in selected_ids)
        and (args.include_disabled or source.get("enabled", True))
    ]
    missing = selected_ids - {source["id"] for source in sources}
    if missing:
        parser.error(f"unknown source id(s): {', '.join(sorted(missing))}")

    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as pool:
        jobs = {pool.submit(collect_source, source, local_tz): source for source in chosen}
        for job in as_completed(jobs):
            source = jobs[job]
            try:
                items = job.result()
            except Exception as exc:
                errors.append(f"{source['id']}: {exc}")
                continue
            for item in items:
                published = item.pop("published_at")
                if published is None or not (start <= published < end):
                    continue
                local_published = published.astimezone(local_tz)
                rows.append(
                    {
                        "source_id": source["id"],
                        "source_name": source["name"],
                        "source_tier": source["tier"],
                        "owner_key": source["owner_key"],
                        "participation": source["participation"],
                        "topics": source.get("topics", []),
                        "published_at": published.isoformat(),
                        "local_date": local_published.date().isoformat(),
                        **item,
                    }
                )

    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        unique[(row["source_id"], row["url"])] = row
    rows = sorted(unique.values(), key=lambda row: row["published_at"], reverse=True)

    if args.format == "json":
        rendered = json.dumps(rows, ensure_ascii=False, indent=2)
    elif args.format == "table":
        rendered = render_table(rows)
    else:
        rendered = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + ("\n" if rendered else ""), encoding="utf-8")
    else:
        print(rendered)

    for error in errors:
        print(f"warning: {error}", file=sys.stderr)
    print(
        f"collected {len(rows)} items from {len(chosen)} sources "
        f"for {args.from_day.isoformat()}..{args.to_day.isoformat()} ({timezone_name})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
