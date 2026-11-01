import unittest

from app import db, matching


class MatchingTests(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        db.seed(self.conn)

    def _id(self, table, col, value):
        return self.conn.execute(f"SELECT id FROM {table} WHERE {col} = ?", (value,)).fetchone()["id"]

    def test_sherlock_tops_backend_detective(self):
        job = self._id("jobs", "title", "Backend Detective")
        result = matching.matches_for_job(self.conn, job)
        self.assertEqual(result[0]["name"], "Sherlock H.")
        # full skills (60) + full experience (25) + 1/2 culture (5) + immediate (5)
        self.assertEqual(result[0]["score"], 95.0)

    def test_incident_commander_prefers_olivia_or_katniss(self):
        job = self._id("jobs", "title", "Incident Commander")
        top2 = {m["name"] for m in matching.matches_for_job(self.conn, job)[:2]}
        self.assertEqual(top2, {"Olivia P.", "Katniss E."})

    def test_candidate_direction(self):
        cand = self._id("candidates", "name", "Michael S.")
        result = matching.matches_for_candidate(self.conn, cand)
        self.assertEqual(result[0]["title"], "Sales Engineer")

    def test_scores_sorted_and_complete(self):
        job = self._id("jobs", "title", "Sales Engineer")
        result = matching.matches_for_job(self.conn, job)
        self.assertEqual(len(result), 15)
        scores = [m["score"] for m in result]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_unknown_ids(self):
        self.assertIsNone(matching.matches_for_job(self.conn, 9999))
        self.assertIsNone(matching.matches_for_candidate(self.conn, 9999))


if __name__ == "__main__":
    unittest.main()
