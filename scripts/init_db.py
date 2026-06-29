#!/usr/bin/env python3
"""Execute SQL schema properly, handling multi-line statements."""
import re
import pymysql

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3308,
    "user": "root",
    "password": "LeanPortal2024!",
    "database": "fundbotai",
}


def parse_sql_script(sql: str):
    """Split SQL into individual statements, respecting quoted strings with semicolons."""
    statements = []
    current = []
    in_string = None
    escape = False

    for ch in sql:
        if escape:
            current.append(ch)
            escape = False
            continue

        if ch == "\\" and in_string:
            current.append(ch)
            escape = True
            continue

        if ch in ("'", '"') and (in_string is None or ch == in_string):
            if in_string is None:
                in_string = ch
            else:
                in_string = None
            current.append(ch)
            continue

        if ch == ";" and in_string is None:
            stmt = "".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
            continue

        current.append(ch)

    stmt = "".join(current).strip()
    if stmt:
        statements.append(stmt)

    return statements


def main():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    with open("/home/dennis/fundbotai/database/init/01_schema.sql") as f:
        sql = f.read()

    # Remove comments
    sql = re.sub(r"--[^\n]*", "", sql)

    statements = parse_sql_script(sql)

    executed = 0
    errors = 0
    for i, stmt in enumerate(statements):
        try:
            cursor.execute(stmt)
            executed += 1
        except Exception as e:
            error_msg = str(e)
            # Skip "already exists" errors
            if "already exists" in error_msg.lower():
                executed += 1
                continue
            print(f"  ERR[{i}]: {error_msg[:100]}")
            errors += 1

    conn.commit()

    # Verify
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"\nTables created: {len(tables)}")
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t[0]}")
        c = cursor.fetchone()[0]
        print(f"  {t[0]}: {c} rows")

    cursor.close()
    conn.close()
    print(f"\nDone: {executed} OK, {errors} errors")


if __name__ == "__main__":
    main()
