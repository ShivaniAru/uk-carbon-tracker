"""UK grid carbon intensity collector.

Usage:
    python collector.py backfill   # load last 13 days of history (run once)
    python collector.py            # save the current half-hour (run every 30 min)

Data: National Grid ESO Carbon Intensity API (free, no key). https://carbon-intensity.github.io/api-definitions/
"""
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

import requests

BASE = "https://api.carbonintensity.org.uk"
DB = "carbon.db"
FMT = "%Y-%m-%dT%H:%MZ"


def get(path):
    r = requests.get(BASE + path, timeout=30, headers={"Accept": "application/json"})
    r.raise_for_status()
    return r.json()["data"]


def init_db(con):
    con.execute("""CREATE TABLE IF NOT EXISTS intensity(
        from_ts TEXT PRIMARY KEY, to_ts TEXT, forecast INTEGER, actual INTEGER, idx TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS mix(
        from_ts TEXT, fuel TEXT, perc REAL, PRIMARY KEY(from_ts, fuel))""")
    con.commit()


def save_intensity(con, rows):
    con.executemany(
        "INSERT OR REPLACE INTO intensity VALUES (?,?,?,?,?)",
        [(r["from"], r["to"], r["intensity"].get("forecast"),
          r["intensity"].get("actual"), r["intensity"].get("index")) for r in rows])


def save_mix(con, rows):
    con.executemany(
        "INSERT OR REPLACE INTO mix VALUES (?,?,?)",
        [(r["from"], m["fuel"], m["perc"]) for r in rows for m in r["generationmix"]])


def collect_now(con):
    save_intensity(con, get("/intensity"))
    save_mix(con, [get("/generation")])
    con.commit()
    print("Saved current half-hour at", datetime.now(timezone.utc).isoformat(timespec="seconds"))


def backfill(con, days=13):
    """The API allows at most 14 days per request, so go in 7-day chunks."""
    end = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    start = end - timedelta(days=days)
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=7), end)
        span = f"/{cur.strftime(FMT)}/{nxt.strftime(FMT)}"
        save_intensity(con, get("/intensity" + span))
        save_mix(con, get("/generation" + span))
        con.commit()
        print("Backfilled", cur.date(), "->", nxt.date())
        cur = nxt


if __name__ == "__main__":
    con = sqlite3.connect(DB)
    init_db(con)
    if len(sys.argv) > 1 and sys.argv[1] == "backfill":
        backfill(con)
    else:
        collect_now(con)
    con.close()
