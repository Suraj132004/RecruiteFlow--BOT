# Recruiter Bot — Backend Assignment (minimal version)

A small backend that loads fictional candidates and jobs, then ranks matches in both directions.
Python 3.9+ standard library only (`sqlite3` + `http.server`) — **no pip install, no ORM**; every query is hand-written SQL.

## Layout

```
app/schema.sql      hand-written DDL
app/seed_data.py    candidates + jobs from the brief
app/db.py           connection, schema load, seeding (raw SQL)
app/matching.py     matching SQL + scoring function
app/server.py       JSON HTTP API
run.py              entry point
tests/              unit tests
sql/sql_detective.sql   Part 2 answers (Q1–Q5)
sql/detective_setup.sql Part 2 schema + data, loaded as-is
```

## Run

```bash
python3 run.py                # http://127.0.0.1:8000, auto-seeds an empty DB
python3 run.py --port 9000 --db my.db
python3 -m unittest discover -s tests -t .
```

## API

```bash
curl localhost:8000/jobs                      # list jobs (ids)
curl localhost:8000/candidates                # list candidates (ids)
curl localhost:8000/jobs/1/matches            # ranked candidates for a job
curl localhost:8000/candidates/11/matches     # ranked jobs for a candidate
curl -X POST localhost:8000/seed              # wipe + reload seed data
```

Each match: `{"name"/"title": ..., "score": 0-100, "reason": "3/3 required skills (...); 8y experience vs 3y min; ..."}`.
Unknown ids return 404.

## Part 2 — SQL Detective

```bash
sqlite3 :memory: ".read sql/detective_setup.sql" ".read sql/sql_detective.sql"
```
Q3 treats `Ananya.Rao@mail.com` and `ananya.rao@mail.com` as one person (identity = `lower(trim(email))`);
"applied to a posting" is inferred from interviews, the only applicant→posting link in the data.
Q2 counts anyone with a Final interview row (any outcome) as having "reached" Final.

## Decisions and trade-offs

**Schema.** Skills are normalised into a `skills` table with join tables for candidates and jobs, so overlap is a
plain SQL join rather than string parsing. Traits and culture keywords are small join tables. Matches are **not
stored**: they are computed on demand, so they can never go stale when a candidate or job changes. With ~15×6
pairs this is instant; at scale I would materialise scores and refresh on write.

**Algorithm.** `score = 100 × (0.60·skills + 0.25·experience + 0.10·culture + 0.05·availability)`
- *skills* = matched required skills ÷ required skills. Weighted highest because it is the core fit signal.
- *experience* = 1.0 if candidate meets the minimum, otherwise `years ÷ min` (linear partial credit). Being
  overqualified is not penalised — that is a seniority/comp question, not a fit one.
- *culture* = job culture keywords that appear in the candidate's traits ÷ keywords. Exact string match only, so
  it is a weak signal (hence 10%); fuzzy/semantic matching would be the next step.
- *availability* = Immediate 1.0, 2 weeks 0.5, Not looking 0. Small weight on purpose: "Not looking" candidates
  are still listed (they can be nudged) but rank slightly lower.
- Ties break on more experience, then name (jobs direction) or title (candidates direction) for deterministic output.

Known weakness: a candidate with zero skill overlap but lots of experience still gets ~30 points (experience +
availability). A hard "at least one skill matches" floor would be a one-line change; I left scores continuous so
the ranking always returns everyone.

## AI tools

I used an AI assistant (Claude) to scaffold the code and SQL. I reviewed the scoring weights and the SQL results by
hand (e.g. verified Q4 conversion rates against the raw interview rows), and I am prepared to explain every part.
