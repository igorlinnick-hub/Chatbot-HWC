"""
End-to-end test for the Antonia conversation engine.
Run with: python test_conversation.py

Requires: ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY in .env
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from bot.conversation import generate_response, send_opener

TEST_PLATFORM = "telegram"
TEST_USER_ID = "test_user_001"

# Simulated client conversation
TEST_FLOW = [
    "here for content mostly but also yeah anxiety is a thing",
    "mostly in social situations, like meeting new people or dates",
    "honestly I'd just feel free, like I could actually be myself",
    "I think I've just gotten used to it, like it's just who I am",
    "pretty important honestly, I'm tired of it holding me back",
    "yeah sure",
    "yes that sounds good",
    "yeah I have time",
]


async def run_test():
    print("\n" + "=" * 60)
    print("ANTONIA BOT — END TO END TEST")
    print("=" * 60 + "\n")

    # Step 1 — opener
    print(">>> New conversation detected")
    result = await send_opener(TEST_PLATFORM, TEST_USER_ID)
    for msg in result["messages"]:
        print(f"\nBOT: {msg}")
    print(f"   [step: {result['step']}]")

    # Steps 2-9
    for user_msg in TEST_FLOW:
        print(f"\nCLIENT: {user_msg}")
        result = await generate_response(TEST_PLATFORM, TEST_USER_ID, user_msg)

        for msg in result["messages"]:
            print(f"\nBOT: {msg}")

        print(f"   [step: {result['step']}]")

        if result["handoff"]:
            print(f"\n!! HANDOFF TRIGGERED: {result['handoff_type']}")
            print(f"   Summary: {result['handoff_summary']}")
            break

        if result["step"] == 9:
            print("\n>> BOOKING COMPLETE")
            break

        await asyncio.sleep(0.5)

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_test())
