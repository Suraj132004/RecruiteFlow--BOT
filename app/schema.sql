-- Recruiter Bot schema (hand-written DDL, SQLite)
-- Matches are not stored: they are derived on demand from the tables below,
-- so they can never go stale when candidates or jobs change.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS skills (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS candidates (
    id               INTEGER PRIMARY KEY,
    name             TEXT NOT NULL,
    experience_years INTEGER NOT NULL CHECK (experience_years >= 0),
    availability     TEXT NOT NULL CHECK (availability IN ('Immediate', '2 weeks', 'Not looking')),
    quirk            TEXT
);

CREATE TABLE IF NOT EXISTS candidate_skills (
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    skill_id     INTEGER NOT NULL REFERENCES skills(id),
    PRIMARY KEY (candidate_id, skill_id)
);

CREATE TABLE IF NOT EXISTS candidate_traits (
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    trait        TEXT NOT NULL,
    PRIMARY KEY (candidate_id, trait)
);

CREATE TABLE IF NOT EXISTS jobs (
    id             INTEGER PRIMARY KEY,
    title          TEXT NOT NULL,
    min_experience INTEGER NOT NULL CHECK (min_experience >= 0),
    tagline        TEXT
);

CREATE TABLE IF NOT EXISTS job_skills (
    job_id   INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skills(id),
    PRIMARY KEY (job_id, skill_id)
);

CREATE TABLE IF NOT EXISTS job_culture (
    job_id  INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    keyword TEXT NOT NULL,
    PRIMARY KEY (job_id, keyword)
);
