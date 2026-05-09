#!/usr/bin/env python3
"""Search the local Open Dental query examples snapshot."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFS = ROOT / "references"
SOURCE_HTML = REFS / "opendental_query_examples_snapshot.html"
QUERY_JSON = REFS / "query_examples.json"
QUERY_INDEX = REFS / "query_examples_index.md"
SOURCE_URL = "https://opendentalsoft.com:1943/ODQueryList/QueryList.aspx"


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data:
            self.parts.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "br":
            self.parts.append("\n")

    def text(self) -> str:
        value = " ".join(part.strip() for part in self.parts if part.strip())
        return re.sub(r"[ \t]+", " ", value).strip()


def strip_tags(fragment: str) -> str:
    parser = TextExtractor()
    parser.feed(fragment)
    return html.unescape(parser.text())


def normalize_sql(value: str) -> str:
    return html.unescape(value).replace("\r\n", "\n").replace("\r", "\n").strip()


def parse_examples() -> list[dict[str, object]]:
    if not SOURCE_HTML.exists():
        fetch_source()
    text = SOURCE_HTML.read_text(encoding="utf-8", errors="replace")
    block_re = re.compile(
        r'<input type="button"[^>]*value="(?P<id>\d+)"[^>]*>\s*</td>'
        r'<td[^>]*>(?P<meta>.*?)</td>\s*</tr><tr>\s*'
        r'<td></td><td[^>]*><textarea[^>]*>(?P<sql>.*?)</textarea>',
        re.S | re.I,
    )
    rows: list[dict[str, object]] = []
    for match in block_re.finditer(text):
        spans = re.findall(r"<span[^>]*>(.*?)</span>", match.group("meta"), flags=re.S | re.I)
        span_text = [strip_tags(span) for span in spans]
        title = span_text[0] if span_text else strip_tags(match.group("meta"))
        notes = " ".join(part for part in span_text[1:] if part).strip()
        dbms = ""
        dbms_match = re.search(r"DBMS version\(s\):\s*([^-\n\r]+)", notes)
        if dbms_match:
            dbms = dbms_match.group(1).strip()
            notes = re.sub(r"\s*DBMS version\(s\):\s*[^-\n\r]+", "", notes).strip()
        sql = normalize_sql(match.group("sql"))
        rows.append(
            {
                "id": int(match.group("id")),
                "title": title,
                "notes": notes.lstrip("- ").strip(),
                "dbms": dbms,
                "sql": sql,
            }
        )
    return rows


def fetch_source() -> None:
    REFS.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        SOURCE_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 Chrome/124 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        SOURCE_HTML.write_bytes(response.read())


def build_index() -> None:
    rows = parse_examples()
    QUERY_JSON.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Open Dental Query Examples Snapshot",
        "",
        f"Source: {SOURCE_HTML.name}",
        f"Parsed examples: {len(rows)}",
        "",
        "| ID | Title | DBMS | Notes |",
        "|---:|---|---|---|",
    ]
    for row in rows:
        title = str(row["title"]).replace("|", "\\|")
        dbms = str(row["dbms"]).replace("|", "\\|")
        notes = str(row["notes"]).replace("|", "\\|")
        if len(notes) > 240:
            notes = notes[:237] + "..."
        lines.append(f"| {row['id']} | {title} | {dbms} | {notes} |")
    QUERY_INDEX.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_rows() -> list[dict[str, object]]:
    if not QUERY_JSON.exists():
        build_index()
    return json.loads(QUERY_JSON.read_text(encoding="utf-8"))


def score(haystack: str, terms: list[str]) -> int:
    lowered = haystack.lower()
    total = 0
    for term in terms:
        needle = term.lower().strip()
        if not needle:
            continue
        total += lowered.count(needle)
        if re.search(rf"\b{re.escape(needle)}\b", lowered):
            total += 5
    return total


def matches_dbms(row: dict[str, object], dbms: str | None) -> bool:
    if not dbms:
        return True
    wanted = dbms.lower()
    current = str(row.get("dbms", "")).lower()
    if wanted in {"mysql", "mysql5", "mysql 5", "mysql 5.x"}:
        return "mysql 5.x" in current
    if wanted in {"mariadb", "mariadb10", "mariadb 10", "mariadb 10.x"}:
        return "mariadb 10.x" in current
    return wanted in current


def cmd_examples(args: argparse.Namespace) -> int:
    rows = load_rows()
    hits = []
    for row in rows:
        if not matches_dbms(row, args.dbms):
            continue
        haystack = f"{row['id']} {row['title']} {row['notes']} {row['dbms']} {row['sql']}"
        hit_score = score(haystack, args.terms)
        if hit_score:
            hits.append((hit_score, row))
    hits.sort(key=lambda item: (-item[0], int(item[1]["id"])))
    for _, row in hits[: args.limit]:
        print(f"#{row['id']} {row['title']}")
        if row["dbms"]:
            print(f"DBMS: {row['dbms']}")
        if row["notes"]:
            print(f"Notes: {row['notes']}")
        if args.sql:
            print()
            print(row["sql"])
            print("\n---")
        else:
            print()
    return 0


def cmd_id(args: argparse.Namespace) -> int:
    rows = load_rows()
    for row in rows:
        if int(row["id"]) == args.query_id:
            if args.sql_only:
                print(row["sql"])
                return 0
            print(f"#{row['id']} {row['title']}")
            if row["dbms"]:
                print(f"DBMS: {row['dbms']}")
            if row["notes"]:
                print(f"Notes: {row['notes']}")
            print()
            print(row["sql"])
            return 0
    print(f"QueryID {args.query_id} not found", file=sys.stderr)
    return 1


def cmd_stats(args: argparse.Namespace) -> int:
    rows = load_rows()
    mysql = sum(1 for row in rows if matches_dbms(row, "mysql"))
    mariadb = sum(1 for row in rows if matches_dbms(row, "mariadb"))
    both = sum(1 for row in rows if matches_dbms(row, "mysql") and matches_dbms(row, "mariadb"))
    print(f"examples={len(rows)}")
    print(f"mysql_5_x={mysql}")
    print(f"mariadb_10_x={mariadb}")
    print(f"both={both}")
    if rows:
        print(f"first_id={rows[0]['id']}")
        print(f"last_id={rows[-1]['id']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build-index")
    build.set_defaults(func=lambda args: (build_index() or 0))

    fetch = sub.add_parser("fetch-source")
    fetch.set_defaults(func=lambda args: (fetch_source() or 0))

    examples = sub.add_parser("examples")
    examples.add_argument("terms", nargs="+")
    examples.add_argument("--dbms", choices=["mysql", "mariadb", "mysql 5.x", "mariadb 10.x"])
    examples.add_argument("--limit", type=int, default=10)
    examples.add_argument("--sql", action="store_true")
    examples.set_defaults(func=cmd_examples)

    by_id = sub.add_parser("id")
    by_id.add_argument("query_id", type=int)
    by_id.add_argument("--sql-only", action="store_true")
    by_id.set_defaults(func=cmd_id)

    stats = sub.add_parser("stats")
    stats.set_defaults(func=cmd_stats)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
