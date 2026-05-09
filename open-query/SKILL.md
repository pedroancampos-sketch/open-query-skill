---
name: open-query
description: Use only when the user explicitly asks to use or activate "open-query" for Open Dental SQL query generation. Do not auto-activate for generic Open Dental, SQL, dashboard, patient list, or reporting requests unless the user names open-query.
---

# Open Query

This skill is an independent Open Dental query assistant. It is based on a local snapshot of the official Open Dental Query Examples page:

`https://opendentalsoft.com:1943/ODQueryList/QueryList.aspx`

The local reference files contain examples for **MySQL 5.x** and **MariaDB 10.x** after installation bootstrap. Ignore newer site changes unless the user explicitly asks to refresh the snapshot.

## Activation Rule

Use this skill only when the user explicitly requests `open-query`.

## Mandatory Version Question

Before generating SQL, ask which database version is being used if the user has not already said it:

`Qual versao do banco voce esta usando: MySQL 5.x ou MariaDB 10.x?`

Do not draft SQL until the user provides one of those versions.

## Output Rule

When producing a query, output **only pure SQL**:

- No Markdown fences.
- No explanation.
- No bullets.
- No comments outside the SQL.
- SQL comments are allowed only inside the SQL when they are necessary for variables or non-obvious logic.

If the request is ambiguous enough that SQL would likely be wrong, ask the minimum clarification question first.

## References

- `references/opendental_query_examples_snapshot.html`: raw official snapshot.
- `references/query_examples.json`: parsed examples with ID, title, notes, DBMS, and SQL.
- `references/query_examples_index.md`: compact searchable index.
- `references/source_notes.md`: source and snapshot notes.

If the snapshot/index files are missing, run:

```bash
scripts/bootstrap_references.sh
```

## Search Workflow

Use the bundled script before drafting SQL:

```bash
scripts/search_open_query.py stats
scripts/search_open_query.py fetch-source
scripts/search_open_query.py build-index
scripts/search_open_query.py examples "recall" "appointment" --dbms mariadb --limit 10
scripts/search_open_query.py examples "treatment planned" --dbms mysql --limit 5 --sql
scripts/search_open_query.py id 1058
scripts/search_open_query.py id 1058 --sql-only
```

Use examples from the same DBMS whenever possible. If a useful example exists only for the other DBMS, adapt cautiously and keep syntax compatible with the user's stated version.

## Query Design Rules

- Generate read-only SQL unless the user explicitly requests otherwise and the environment permits it.
- Prefer stable patient identifiers such as `PatNum`, `ChartNumber`, and clear patient names.
- Do not use `SELECT *` for final user-facing queries unless requested.
- Use explicit joins and readable aliases.
- Include practical `ORDER BY`.
- Add date variables at the top when the report depends on ranges.
- For large datetime columns, prefer range filters over wrapping columns in functions.
- Preserve the requested DBMS version: MySQL 5.x syntax can be more limited than MariaDB 10.x.
- Do not mention implementation reasoning in the final output; final output is SQL only.

## Refresh Policy

Do not update the snapshot or indexes automatically. The user said to ignore new changes. Refresh only if the user explicitly asks to update the open-query skill data.
