"""Matching: raw SQL gathers the raw signals, a small pure function turns them into a score."""
import sqlite3

# Weights sum to 1.0. Skills dominate; experience is the second hard-ish requirement.
W_SKILLS, W_EXPERIENCE, W_CULTURE, W_AVAILABILITY = 0.60, 0.25, 0.10, 0.05
AVAILABILITY_SCORE = {"Immediate": 1.0, "2 weeks": 0.5, "Not looking": 0.0}

# One query shape for both directions: one row per (candidate, job) pair, filtered by :job_id / :candidate_id.
# NULL filter parameter means "no filter" so the same SQL serves both endpoints.
PAIR_SQL = """
SELECT
    c.id AS candidate_id, c.name AS candidate_name, c.experience_years, c.availability,
    j.id AS job_id, j.title AS job_title, j.min_experience,
    (SELECT COUNT(*) FROM job_skills WHERE job_id = j.id) AS required_skills,
    (SELECT COUNT(*) FROM job_skills js JOIN candidate_skills cs ON cs.skill_id = js.skill_id
      WHERE js.job_id = j.id AND cs.candidate_id = c.id) AS matched_skills,
    (SELECT group_concat(s.name, ', ') FROM job_skills js
       JOIN candidate_skills cs ON cs.skill_id = js.skill_id
       JOIN skills s ON s.id = js.skill_id
      WHERE js.job_id = j.id AND cs.candidate_id = c.id) AS matched_skill_names,
    (SELECT COUNT(*) FROM job_culture jc JOIN candidate_traits ct ON ct.trait = jc.keyword
      WHERE jc.job_id = j.id AND ct.candidate_id = c.id) AS culture_hits,
    (SELECT COUNT(*) FROM job_culture WHERE job_id = j.id) AS culture_keywords
FROM candidates c CROSS JOIN jobs j
WHERE (:job_id IS NULL OR j.id = :job_id)
  AND (:candidate_id IS NULL OR c.id = :candidate_id)
"""


def score_pair(row: sqlite3.Row) -> tuple[float, str]:
    skills = row["matched_skills"] / row["required_skills"] if row["required_skills"] else 0.0
    # Meeting the minimum gives full marks; below it, credit scales linearly. Overqualified is not penalised.
    exp = 1.0 if row["min_experience"] == 0 else min(1.0, row["experience_years"] / row["min_experience"])
    culture = row["culture_hits"] / row["culture_keywords"] if row["culture_keywords"] else 0.0
    avail = AVAILABILITY_SCORE[row["availability"]]

    score = round(100 * (W_SKILLS * skills + W_EXPERIENCE * exp + W_CULTURE * culture + W_AVAILABILITY * avail), 1)

    matched = row["matched_skill_names"] or "none"
    reason = (f"{row['matched_skills']}/{row['required_skills']} required skills ({matched}); "
              f"{row['experience_years']}y experience vs {row['min_experience']}y min; "
              f"{row['culture_hits']}/{row['culture_keywords']} culture traits; {row['availability']}")
    return score, reason


def _rank(conn, job_id=None, candidate_id=None):
    rows = conn.execute(PAIR_SQL, {"job_id": job_id, "candidate_id": candidate_id}).fetchall()
    out = []
    for r in rows:
        score, reason = score_pair(r)
        out.append((score, r, reason))
    return out


def matches_for_job(conn, job_id: int):
    if conn.execute("SELECT 1 FROM jobs WHERE id = ?", (job_id,)).fetchone() is None:
        return None
    ranked = _rank(conn, job_id=job_id)
    # Tie-break: more experience first, then name, so output is deterministic.
    ranked.sort(key=lambda t: (-t[0], -t[1]["experience_years"], t[1]["candidate_name"]))
    return [{"candidate_id": r["candidate_id"], "name": r["candidate_name"], "score": s, "reason": why}
            for s, r, why in ranked]


def matches_for_candidate(conn, candidate_id: int):
    if conn.execute("SELECT 1 FROM candidates WHERE id = ?", (candidate_id,)).fetchone() is None:
        return None
    ranked = _rank(conn, candidate_id=candidate_id)
    ranked.sort(key=lambda t: (-t[0], t[1]["job_title"]))
    return [{"job_id": r["job_id"], "title": r["job_title"], "score": s, "reason": why}
            for s, r, why in ranked]
