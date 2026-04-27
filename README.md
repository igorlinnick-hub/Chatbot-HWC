# Hawaii Wellness Clinic — Instagram Intake Bot

Conversational AI assistant ("Leilani") that handles Instagram DM intake for Hawaii Wellness Clinic.
The bot mirrors the client, follows a 9-step qualifier, and books a free 15-minute discovery call
via the clinic's calendar link. A web dashboard (Next.js, Vercel) gives the team a place to monitor
conversations, take over manually, correct replies, and add training examples.

Instagram traffic is routed through **ManyChat** — ManyChat is the source of truth for outbound
sending and timing; this backend is the brain that decides what to say.

---

## Repo layout

```
.
├── main.py                  FastAPI app: webhook entry points, scheduler, practice endpoints
├── config.py                Env vars
├── requirements.txt
├── railway.toml             Railway deploy config (uvicorn)
├── bot/
│   ├── conversation.py      Claude call, validation, step advancement, handoff detection
│   ├── instagram.py         Meta Graph API (typing indicator + send)
│   ├── delay_engine.py      Natural delay calc + night-hours hold
│   └── handoff.py           Marks conversations handed_off + writes metadata.handoff
├── prompts/
│   ├── system_prompt.py     Persona + global rules (Leilani / Hawaii Wellness)
│   ├── steps.py             9-step script
│   └── prompt_builder.py    Per-step instructions + dynamic injection of corrections + examples
├── db/
│   ├── schema.sql           Run this in Supabase SQL editor on a fresh project
│   └── supabase_client.py   All DB reads/writes
├── test_conversation.py     Local end-to-end test of the conversation engine
├── wipe_training_data.py    One-shot: clear corrections + training_examples
└── dashboard/               Next.js admin (see dashboard/README.md)
```

---

## How a message flows

1. A user replies to the clinic's Instagram DM.
2. **ManyChat** receives the message (Instagram → ManyChat integration).
3. ManyChat forwards it to this backend via an **External Request** to `POST /webhook/manychat`.
4. Backend looks up the conversation in Supabase, calls Claude with full history + injected
   corrections + training examples, advances the script step, and returns a ManyChat v2 response
   payload.
5. ManyChat sends the message(s) to the user with its own Smart Delay.
6. Anything the team should see (new handoffs, booked calls, corrections that need adding) shows
   up in the dashboard.

The direct `/webhook/instagram` endpoint exists as a fallback if you ever bypass ManyChat — it
uses an internal delay engine + `bot/instagram.py` for sending. In ManyChat-mode it's not used.

---

## Setup (for the developer)

### 1. Supabase

Create a project. In the SQL editor run `db/schema.sql`. Grab `SUPABASE_URL` and the
`service_role` key from Project Settings → API.

### 2. Backend (FastAPI)

```bash
cd Antonia
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # fill in keys
uvicorn main:app --reload
```

Local URL: `http://localhost:8000`.
Health check: `GET /health`.

#### Required env vars (`.env`)

| Key                            | What it is                                                          |
|--------------------------------|---------------------------------------------------------------------|
| `ANTHROPIC_API_KEY`            | Claude API key. Model: `claude-sonnet-4-6`.                         |
| `INSTAGRAM_PAGE_ACCESS_TOKEN`  | Meta — only needed for the direct `/webhook/instagram` fallback.    |
| `INSTAGRAM_APP_SECRET`         | Meta — webhook signature verification (currently disabled in code). |
| `INSTAGRAM_VERIFY_TOKEN`       | Any random string, used by Meta to verify the webhook on setup.     |
| `INSTAGRAM_PAGE_ID`            | Filters out echo messages from the page itself.                     |
| `SUPABASE_URL`                 | Supabase project URL.                                               |
| `SUPABASE_KEY`                 | Supabase **service_role** key (not anon).                           |
| `BOOKING_LINK`                 | Calendar URL the bot sends at step 9 (Calendly, Cal.com, etc.).     |

Deploy: a `railway.toml` is already set up. Push the repo to Railway and set the same env vars
there. Backend needs to be reachable from ManyChat (public HTTPS URL).

### 3. ManyChat configuration

Inside ManyChat:

1. Connect the Instagram page.
2. In the flow that triggers on every incoming Instagram DM, add an **External Request** action:
   - Method: `POST`
   - URL: `https://<your-backend-domain>/webhook/manychat`
   - Headers: `Content-Type: application/json`
   - Body (JSON):
     ```json
     {
       "subscriber_id": "{{subscriber id}}",
       "last_input_text": "{{last input text}}"
     }
     ```
   - Response handling: ManyChat v2 — wire the External Request response straight into a
     "Send a Message" block that uses the returned messages.
3. Make sure ManyChat itself sends the very first opener message when someone DMs the page for
   the first time (the backend treats that as already-sent and starts the conversation from the
   user's reply to it).

Trigger words like `start`, `hello`, `hi`, `hey` are filtered server-side and won't trigger a
Claude call — they're ManyChat keyword triggers, not real user input.

### 4. Dashboard (Next.js)

See `dashboard/README.md`. TL;DR:

```bash
cd dashboard
npm install
cp .env.example .env.local      # fill in Supabase + dashboard password
npm run dev
```

Deploy: Vercel. Connect the repo, set the dashboard subdirectory as the project root, and set the
same env vars in Vercel.

---

## Operating the bot

- **Toggle the bot on/off** from the dashboard home page (`bot_settings` table).
- **Take over a conversation** from the conversation detail page — bot stops responding until you
  press Resume.
- **Correct a reply** from `/corrections` — gets injected into the next Claude call. No deploy.
- **Add a training example** from `/training` — same.
- **Practice** with the bot in `/practice` without affecting any real conversation
  (writes go under `platform = 'practice'` and are filtered out of stats and the conversations
  list).
- **Wipe training data**: `python wipe_training_data.py` (use after switching domains).

## Handoff signals

Claude can emit two tokens at the end of any reply, which the engine catches and converts to a
status flip + `metadata.handoff` write:

- `[URGENT_HANDOFF: reason]` — active panic, self-harm, medical emergency.
- `[OWNER_HANDOFF: reason]` — bot is uncertain or the user has refused twice on a gated step.

Both surface in the dashboard as a banner on the conversation detail page.

## Things explicitly removed / out of scope

- **Telegram** — fully removed. No bot, no notifier, no env vars.
- **Personal practice training corpus** — wiped. The clinic teaches the bot through the dashboard.
- **Direct medical advice** — the prompt forbids it. The bot books a discovery call with a real
  coach instead.

## Test the engine locally

```bash
python test_conversation.py
```

Runs the full 1→9 script against Claude using a fake user_id. Requires Supabase + Anthropic env
vars set. Writes one row to `conversations` (user_id `test_user_001`, platform `instagram`).
