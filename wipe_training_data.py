#!/usr/bin/env python3
"""
Delete every row from the corrections and training_examples tables.

Use this once after switching the bot's domain (e.g. to wipe the previous
practice's training corpus before the new business teaches its own).

Run:  python wipe_training_data.py
Requires SUPABASE_URL + SUPABASE_KEY in .env.
"""

import sys

from supabase import create_client

from config import SUPABASE_URL, SUPABASE_KEY


def main() -> int:
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Missing SUPABASE_URL or SUPABASE_KEY in .env", file=sys.stderr)
        return 1

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    confirm = input(
        "This will DELETE every row in `corrections` and `training_examples`.\n"
        "Type 'wipe' to confirm: "
    ).strip()
    if confirm != "wipe":
        print("Aborted.")
        return 1

    corrections = supabase.table("corrections").delete().neq("id", 0).execute()
    examples = supabase.table("training_examples").delete().neq("id", 0).execute()

    print(f"Deleted {len(corrections.data)} corrections.")
    print(f"Deleted {len(examples.data)} training examples.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
