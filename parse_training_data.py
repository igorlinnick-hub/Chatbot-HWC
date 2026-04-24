#!/usr/bin/env python3
"""
Parse Instagram DM HTML files to extract high-quality training examples
for an anxiety hypnotherapist chatbot (Antonia).
"""

import os
import re
import json
from html.parser import HTMLParser
from pathlib import Path


INBOX_DIR = Path(
    "/Users/igorlinnik/Documents/Code Projects/Chat Bots/"
    "instagram-hypnowithantonia-2026-03-20-fTWUwpFR/"
    "your_instagram_activity/messages/inbox"
)

ANTONIA_NAME = "Antonia Zachariadou"

KEYWORDS = [
    "anxiety", "social anxiety", "confidence", "self-esteem", "self esteem",
    "panic", "stress", "relationship", "fear", "nervous", "therapy",
    "hypnotherapy", "session", "booking", "help", "struggling", "stuck",
    "overwhelmed", "worried", "insomnia", "sleep", "phobia", "trauma",
    "anxious", "overthink", "worry", "depressed", "depression", "scared",
    "afraid", "cope", "coping", "mental health", "burnout", "overcome",
]

KEYWORD_PATTERN = re.compile(
    r'\b(?:' + '|'.join(re.escape(k) for k in KEYWORDS) + r')',
    re.IGNORECASE
)


class IGMessageParser(HTMLParser):
    """Parse Instagram DM HTML export to extract messages."""

    def __init__(self):
        super().__init__()
        self.messages = []  # list of (sender, text, timestamp)
        self._in_h2 = False
        self._in_message_div = False
        self._in_timestamp = False
        self._current_sender = ""
        self._current_text_parts = []
        self._current_timestamp = ""
        self._div_depth = 0
        self._capture_text = False
        self._in_main = False
        self._block_classes = ""
        # Track the message block structure
        self._in_msg_block = False
        self._in_content_div = False
        self._content_div_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        classes = attrs_dict.get("class", "")

        if tag == "main":
            self._in_main = True

        if not self._in_main:
            return

        # Message block: div with class containing "pam" and "uiBoxWhite"
        if tag == "div" and "pam" in classes and "uiBoxWhite" in classes:
            self._in_msg_block = True
            self._current_sender = ""
            self._current_text_parts = []
            self._current_timestamp = ""

        if self._in_msg_block:
            if tag == "h2" and "_a6-h" in classes:
                self._in_h2 = True

            # The message text is inside div._a6-p > div > div (2nd child div)
            if tag == "div" and "_a6-p" in classes:
                self._in_content_div = True
                self._content_div_depth = 0

            if self._in_content_div:
                if tag == "div":
                    self._content_div_depth += 1
                    # The actual text is in the 2nd nested div
                    if self._content_div_depth == 3:
                        self._capture_text = True

                if tag == "br":
                    self._current_text_parts.append(" ")

            # Timestamp div
            if tag == "div" and "_a6-o" in classes:
                self._in_timestamp = True

    def handle_endtag(self, tag):
        if not self._in_main:
            return

        if tag == "main":
            self._in_main = False

        if tag == "h2" and self._in_h2:
            self._in_h2 = False

        if self._in_content_div and tag == "div":
            if self._content_div_depth == 3:
                self._capture_text = False
            self._content_div_depth -= 1
            if self._content_div_depth < 0:
                self._in_content_div = False
                self._content_div_depth = 0

        if tag == "div" and self._in_timestamp:
            self._in_timestamp = False

        # End of message block - save it
        if tag == "div" and self._in_msg_block and self._current_sender and self._current_timestamp:
            text = " ".join(self._current_text_parts).strip()
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            if text:
                self.messages.append((self._current_sender, text, self._current_timestamp))
            self._in_msg_block = False

    def handle_data(self, data):
        if not self._in_main:
            return

        if self._in_h2:
            self._current_sender += data.strip()

        if self._capture_text:
            self._current_text_parts.append(data)

        if self._in_timestamp:
            self._current_timestamp += data.strip()


def parse_html_file(filepath):
    """Parse a single HTML file and return list of (sender, text, timestamp)."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return []

    parser = IGMessageParser()
    try:
        parser.feed(content)
    except Exception:
        return []

    return parser.messages


def is_antonia(sender):
    """Check if sender is Antonia."""
    return ANTONIA_NAME.lower() in sender.lower()


def score_reply(reply_text, user_text):
    """Score quality of Antonia's reply. Higher = better."""
    score = 0
    text_lower = reply_text.lower()

    # Length bonus: substantive replies
    if len(reply_text) > 100:
        score += 3
    elif len(reply_text) > 50:
        score += 2
    elif len(reply_text) > 20:
        score += 1

    # Contains a question - shows engagement
    if "?" in reply_text:
        score += 3

    # Empathy markers
    empathy_phrases = [
        "i understand", "i hear you", "that must", "i'm sorry",
        "that sounds", "i can imagine", "it's completely", "it's normal",
        "totally understand", "makes sense", "for sure",
        "must not feel good", "must be", "so exhausting",
    ]
    for phrase in empathy_phrases:
        if phrase in text_lower:
            score += 2
            break

    # Therapy/professional language
    therapy_words = [
        "anxiety", "hypnotherapy", "session", "subconscious",
        "overcome", "manage", "cope", "heal", "transform",
        "nervous system", "pattern", "trigger", "root cause",
    ]
    for word in therapy_words:
        if word in text_lower:
            score += 1

    # Penalize very short/generic responses
    generic = ["ok", "thanks", "thank you", "yes", "no", "sure", "lol",
               "haha", "cool", "nice", "great", "awesome"]
    stripped = reply_text.strip().lower().rstrip("!.,")
    if stripped in generic:
        score -= 5

    # Penalize automated/bot-like messages
    if "you messaged" in text_lower or "because they followed" in text_lower:
        score -= 10

    # Bonus for user message relevance (keyword match)
    user_lower = user_text.lower()
    keyword_count = len(KEYWORD_PATTERN.findall(user_lower))
    score += keyword_count * 2

    return score


def main():
    print(f"Scanning {INBOX_DIR}...", flush=True)

    # Find all message_1.html files
    html_files = []
    for folder in sorted(INBOX_DIR.iterdir()):
        msg_file = folder / "message_1.html"
        if msg_file.exists():
            html_files.append(msg_file)

    print(f"Found {len(html_files)} conversation files.", flush=True)

    all_pairs = []
    conversations_with_keywords = 0

    for i, filepath in enumerate(html_files):
        if (i + 1) % 100 == 0:
            print(f"  Processing {i+1}/{len(html_files)}...", flush=True)

        messages = parse_html_file(filepath)
        if not messages:
            continue

        # Messages are in reverse chronological order in the HTML,
        # so reverse to get chronological order
        messages.reverse()

        # Check if any non-Antonia message contains keywords
        user_messages = [m for m in messages if not is_antonia(m[0])]
        has_keyword = any(KEYWORD_PATTERN.search(m[1]) for m in user_messages)

        if not has_keyword:
            continue

        conversations_with_keywords += 1

        # Extract user-message -> Antonia-reply pairs (chronological)
        for j in range(len(messages) - 1):
            sender_j, text_j, ts_j = messages[j]
            # Look for: user says something -> Antonia replies next
            if is_antonia(sender_j):
                continue

            # User message must contain a keyword
            if not KEYWORD_PATTERN.search(text_j):
                continue

            # Find Antonia's next reply (may be multiple messages away due to
            # consecutive user messages)
            antonia_reply_parts = []
            for k in range(j + 1, len(messages)):
                sender_k, text_k, ts_k = messages[k]
                if is_antonia(sender_k):
                    antonia_reply_parts.append(text_k)
                else:
                    break  # hit another user message

            if not antonia_reply_parts:
                continue

            # Combine consecutive Antonia messages into one reply
            combined_reply = " ".join(antonia_reply_parts)

            # Skip automated messages
            if "you messaged" in combined_reply.lower():
                continue
            if "because they followed" in combined_reply.lower():
                continue

            quality_score = score_reply(combined_reply, text_j)

            all_pairs.append({
                "user_message": text_j,
                "ideal_response": combined_reply,
                "score": quality_score,
                "conversation": filepath.parent.name,
            })

    print(f"\nConversations with keyword matches: {conversations_with_keywords}")
    print(f"Total user->Antonia pairs found: {len(all_pairs)}")

    # Sort by score descending, take top 30
    all_pairs.sort(key=lambda x: x["score"], reverse=True)
    top_30 = all_pairs[:30]

    # Format output
    output = []
    for pair in top_30:
        output.append({
            "user_message": pair["user_message"],
            "ideal_response": pair["ideal_response"],
            "notes": f"real conversation example (score: {pair['score']}, from: {pair['conversation']})",
        })

    print(f"\n=== TOP 30 TRAINING EXAMPLES ===\n")
    print(json.dumps(output, indent=2, ensure_ascii=False))

    return output


if __name__ == "__main__":
    main()
