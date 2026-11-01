import argparse

from app.server import run

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Recruiter Bot API")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--db", default="recruiter_bot.db")
    args = p.parse_args()
    run(port=args.port, db_path=args.db)
