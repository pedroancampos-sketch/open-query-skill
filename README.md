# open-query

`open-query` is a Codex skill for creating pure SQL queries for Open Dental using the official Open Dental Query Examples page as the reference source.

Reference source:

https://opendentalsoft.com:1943/ODQueryList/QueryList.aspx

The skill supports the two database targets used by that page:

- MySQL 5.x
- MariaDB 10.x

## What It Does

- Searches Open Dental query examples by topic, QueryID, or SQL text.
- Keeps MySQL 5.x and MariaDB 10.x differences visible.
- Forces the assistant to ask which database version is being used before writing SQL.
- Produces SQL-only answers when activated.
- Stays independent from any project repository.

## What Is Not Bundled

This repository does not include the downloaded Open Dental query examples or parsed full query dataset. The installer/bootstrap downloads those files from the official Open Dental source on your machine.

Generated local files are ignored by Git:

- `open-query/references/opendental_query_examples_snapshot.html`
- `open-query/references/query_examples.json`
- `open-query/references/query_examples_index.md`

## Installation

Clone the repository:

```bash
git clone https://github.com/pedroancampos-sketch/open-query-skill.git
cd open-query-skill
```

Install the skill into Codex:

```bash
mkdir -p ~/.codex/skills
cp -R open-query ~/.codex/skills/open-query
```

Download and index the official Open Dental query examples:

```bash
cd ~/.codex/skills/open-query
chmod +x scripts/bootstrap_references.sh scripts/search_open_query.py
scripts/bootstrap_references.sh
```

Expected result is a small stats summary like:

```text
examples=1497
mysql_5_x=1433
mariadb_10_x=1497
both=1433
```

The exact counts can change if you intentionally refresh from the live Open Dental page later.

## Usage

Activate the skill explicitly by saying `open-query`.

Example:

```text
Use open-query. I need a query for patients overdue for recall who do not have a future appointment.
```

The skill will ask:

```text
Qual versao do banco voce esta usando: MySQL 5.x ou MariaDB 10.x?
```

After you answer, it should return only SQL.

## Local Search Commands

Search examples:

```bash
~/.codex/skills/open-query/scripts/search_open_query.py examples "recall appointment" --dbms mariadb --limit 10
```

Show SQL for a specific QueryID:

```bash
~/.codex/skills/open-query/scripts/search_open_query.py id 1058 --sql-only
```

Rebuild the local index:

```bash
~/.codex/skills/open-query/scripts/search_open_query.py build-index
```

Refresh from the official page only when you intentionally want newer source data:

```bash
~/.codex/skills/open-query/scripts/bootstrap_references.sh
```

## Skill Behavior

The skill is intentionally strict:

- It should activate only when you explicitly request `open-query`.
- It must ask whether you use MySQL 5.x or MariaDB 10.x before generating SQL.
- Final query answers should be SQL only, without Markdown or explanation.
- It ignores new changes unless you explicitly refresh the local reference data.

## Repository Layout

```text
open-query-skill/
├── README.md
└── open-query/
    ├── SKILL.md
    ├── agents/
    │   └── openai.yaml
    ├── references/
    │   └── source_notes.md
    └── scripts/
        ├── bootstrap_references.sh
        └── search_open_query.py
```
