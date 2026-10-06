"""Load the raw A/B CSV into DuckDB and build the staging and mart layers."""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "marketing_AB.csv.gz"
DB = ROOT / "warehouse" / "ab_test.duckdb"


def build(db_path: Path = DB) -> duckdb.DuckDBPyConnection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    con.execute(
        f"CREATE OR REPLACE TABLE raw_ab AS SELECT * FROM read_csv('{RAW}', header=true)"
    )
    for sql_file in ("01_staging.sql", "02_marts.sql"):
        con.execute((ROOT / "sql" / sql_file).read_text())
    return con


if __name__ == "__main__":
    con = build()
    n = con.execute("SELECT SUM(users) FROM mart_variant_summary").fetchone()[0]
    print(f"Built {DB.relative_to(ROOT)} with {n:,} users")
