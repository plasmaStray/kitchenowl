#!/usr/bin/env python3
"""Export one household's KitchenOwl catalog from its SQLite database."""

import argparse
import json
import sqlite3
from datetime import date
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database",
        default="~/docker/appdata/kitchenowl/database.db",
        help="SQLite database path (default: production path under $HOME)",
    )
    parser.add_argument("--household-id", type=int, required=True)
    parser.add_argument("--snapshot-date", default=date.today().isoformat())
    args = parser.parse_args()

    database = Path(args.database).expanduser().resolve()
    connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        categories = [
            dict(row)
            for row in connection.execute(
                """SELECT id, name, default_key, ordering
                   FROM category WHERE household_id = ? ORDER BY id""",
                (args.household_id,),
            )
        ]
        items = [
            dict(row)
            for row in connection.execute(
                """SELECT i.id, i.name, i.category_id, c.name AS category_name,
                          i."default" AS "default", i.default_key, i.icon,
                          i.ordering, i.support
                   FROM item AS i
                   LEFT JOIN category AS c ON c.id = i.category_id
                   WHERE i.household_id = ? ORDER BY i.id""",
                (args.household_id,),
            )
        ]
    finally:
        connection.close()

    snapshot = {
        "schema_version": 2,
        "snapshot_date": args.snapshot_date,
        "source": {
            "application": "KitchenOwl",
            "household_id": args.household_id,
            "purpose": (
                "catalog restore baseline; excludes lists, users, purchase history "
                "and recipes"
            ),
        },
        "categories": categories,
        "items": items,
    }
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
