#!/usr/bin/env python3
"""Run ad hoc SQL against the project SQLite database.

Examples:
    python dev_sql.py --query "SELECT * FROM player_box_scores LIMIT 5"
    python dev_sql.py --file queries.sql
    python dev_sql.py --list-tables
    python dev_sql.py --schema player_box_scores
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

import pandas as pd


DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "box_scores.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute development SQL queries against the project SQLite database.",
    )
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help="Path to the SQLite database file.",
    )
    parser.add_argument(
        "--query",
        help="SQL query to execute. If omitted, the script reads SQL from stdin.",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Path to a file containing SQL to execute.",
    )
    parser.add_argument(
        "--list-tables",
        action="store_true",
        help="List tables in the database and exit.",
    )
    parser.add_argument(
        "--schema",
        metavar="TABLE",
        help="Show the schema for a table and exit.",
    )
    return parser.parse_args()


def read_sql_text(args: argparse.Namespace) -> str:
    if args.query:
        return args.query.strip()

    if args.file:
        return args.file.read_text(encoding="utf-8").strip()

    if not sys.stdin.isatty():
        return sys.stdin.read().strip()

    raise SystemExit("Provide --query, --file, or pipe SQL into stdin.")


def print_table_list(conn: sqlite3.Connection) -> None:
    tables = pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name",
        conn,
    )
    if tables.empty:
        print("No tables found.")
        return
    print(tables.to_string(index=False))


def print_schema(conn: sqlite3.Connection, table_name: str) -> None:
    schema = pd.read_sql_query(f"PRAGMA table_info({table_name})", conn)
    if schema.empty:
        print(f"No schema found for table: {table_name}")
        return
    print(schema.to_string(index=False))


def is_read_query(sql_text: str) -> bool:
    first_token = sql_text.lstrip().split(None, 1)[0].lower() if sql_text.strip() else ""
    return first_token in {"select", "with", "pragma", "explain"}


def execute_sql(conn: sqlite3.Connection, sql_text: str) -> None:
    if not sql_text:
        raise SystemExit("Empty SQL input.")

    if is_read_query(sql_text):
        result = pd.read_sql_query(sql_text, conn)
        if result.empty:
            print("Query returned no rows.")
        else:
            print(result.to_string(index=False))
        return

    cursor = conn.cursor()
    cursor.execute(sql_text)
    conn.commit()

    rowcount = cursor.rowcount
    if rowcount == -1:
        print("Statement executed successfully.")
    else:
        print(f"Statement executed successfully. Rows affected: {rowcount}")


def main() -> None:
    args = parse_args()
    db_path = Path(args.db).expanduser()

    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")

    with sqlite3.connect(db_path) as conn:
        if args.list_tables:
            print_table_list(conn)
            return

        if args.schema:
            print_schema(conn, args.schema)
            return

        sql_text = read_sql_text(args)
        execute_sql(conn, sql_text)


if __name__ == "__main__":
    main()