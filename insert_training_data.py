#!/usr/bin/env python3
"""Bulk insert parsed training examples into Supabase."""

import sys
sys.path.insert(0, ".")

from parse_training_data import main as parse_main
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

examples = parse_main()

if not examples:
    print("No examples to insert.")
    sys.exit(1)

print(f"\nInserting {len(examples)} training examples into Supabase...")

rows = [
    {
        "user_message": ex["user_message"],
        "ideal_response": ex["ideal_response"],
        "notes": ex["notes"],
    }
    for ex in examples
]

result = supabase.table("training_examples").insert(rows).execute()
print(f"Inserted {len(result.data)} rows into training_examples.")
