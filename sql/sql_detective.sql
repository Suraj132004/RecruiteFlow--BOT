-- Part 2: SQL Detective Challenge (SQLite-compatible; also valid in Postgres/MySQL unless noted)
-- Load schema + seed data from sql/detective_setup.sql first.

-- Q1: All currently open job postings with the owning recruiter.
SELECT jp.id, jp.title, jp.department, jp.opened_date, r.name AS recruiter
FROM job_postings jp
JOIN recruiters r ON r.id = jp.recruiter_id
WHERE jp.status = 'open'
ORDER BY jp.id;

-- Q2: For each job posting, how many applicants reached the Final stage?
-- "Reached" = has a Final interview row (any outcome). Postings with none show 0.
-- COUNT(DISTINCT) guards against an applicant having two Final rows for one posting.
SELECT jp.id, jp.title,
       COUNT(DISTINCT i.applicant_id) AS final_stage_applicants
FROM job_postings jp
LEFT JOIN interviews i ON i.job_posting_id = jp.id AND i.stage = 'Final'
GROUP BY jp.id, jp.title
ORDER BY jp.id;

-- Q3: People who effectively applied to more than one job posting.
-- Data is dirty: the same person appears as separate applicant rows differing only in
-- email case (Ananya Rao, ids 1 and 2). Identity = lower(trim(email)).
-- "Applied to a posting" is inferred from interviews (the only applicant->posting link).
SELECT LOWER(TRIM(a.email)) AS person_email,
       MIN(a.full_name)      AS full_name,
       COUNT(DISTINCT i.job_posting_id) AS postings_applied_to
FROM applicants a
JOIN interviews i ON i.applicant_id = a.id
GROUP BY LOWER(TRIM(a.email))
HAVING COUNT(DISTINCT i.job_posting_id) > 1
ORDER BY person_email;

-- Q4: Final-stage conversion rate per recruiter (passed / total Final interviews),
-- only recruiters with at least 3 Final-stage interviews.
SELECT r.name AS recruiter,
       COUNT(*) AS final_interviews,
       SUM(CASE WHEN i.outcome = 'passed' THEN 1 ELSE 0 END) AS passed,
       ROUND(1.0 * SUM(CASE WHEN i.outcome = 'passed' THEN 1 ELSE 0 END) / COUNT(*), 3) AS conversion_rate
FROM interviews i
JOIN job_postings jp ON jp.id = i.job_posting_id
JOIN recruiters r    ON r.id = jp.recruiter_id
WHERE i.stage = 'Final'
GROUP BY r.id, r.name
HAVING COUNT(*) >= 3
ORDER BY conversion_rate DESC, r.name;

-- Q5 (Bonus): Recruiter with the most successful placements (passed at Final) per department.
-- RANK() keeps ties visible rather than silently dropping one.
WITH placements AS (
    SELECT jp.department, r.name AS recruiter, COUNT(*) AS placements
    FROM interviews i
    JOIN job_postings jp ON jp.id = i.job_posting_id
    JOIN recruiters r    ON r.id = jp.recruiter_id
    WHERE i.stage = 'Final' AND i.outcome = 'passed'
    GROUP BY jp.department, r.id, r.name
),
ranked AS (
    SELECT department, recruiter, placements,
           RANK() OVER (PARTITION BY department ORDER BY placements DESC) AS rnk
    FROM placements
)
SELECT department, recruiter, placements
FROM ranked
WHERE rnk = 1
ORDER BY department;
