import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "finance.db"
SCHEMA = ROOT / "db" / "schema.sql"
SEED = ROOT / "db" / "seed.sql"

def run_script(conn, path: Path):
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()
    conn.executescript(sql)

def main():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys=ON;")
        run_script(conn, SCHEMA)
        run_script(conn, SEED)
        conn.commit()
        print(f"INITIALIZED DB AT {DB_PATH}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
