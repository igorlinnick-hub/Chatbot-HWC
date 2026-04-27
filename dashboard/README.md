# Hawaii Wellness — Bot Dashboard

Admin UI for the Hawaii Wellness Clinic intake bot.
Next.js 14 (App Router), Tailwind, Supabase JS client. Deploys to Vercel.

This is the only admin surface — there is no Telegram admin or CLI. From here the team can:

- Toggle the bot on/off
- Browse conversations + take over / resume
- Review handoffs (urgent + normal) with banner + "mark reviewed"
- Add corrections and training examples (injected into the next Claude call)
- Practice in a sandbox using the real prompt + step logic

The dashboard reads/writes Supabase directly using the `service_role` key. It also calls a
small set of FastAPI endpoints under `/practice/*` for the practice page.

## Stack

- Next.js 14 App Router
- Tailwind CSS
- `@supabase/supabase-js`
- `lucide-react` icons
- Cookie-based password gate (single shared password, `DASHBOARD_PASSWORD`)

## Run locally

```bash
npm install
cp .env.example .env.local
# fill in Supabase + DASHBOARD_PASSWORD + BACKEND_URL
npm run dev
```

`http://localhost:3000`. If `DASHBOARD_PASSWORD` is unset the login gate is skipped and the app
loads directly — useful for development.

If Supabase env vars are missing the dashboard falls back to mock data, so the UI is browsable
without a database.

## Env vars

| Key                          | What it is                                                                       |
|------------------------------|----------------------------------------------------------------------------------|
| `NEXT_PUBLIC_SUPABASE_URL`   | Supabase project URL.                                                            |
| `SUPABASE_SERVICE_ROLE_KEY`  | Supabase **service_role** key.                                                   |
| `DASHBOARD_PASSWORD`         | Shared password to access the dashboard. Unset = no auth (dev only).             |
| `BACKEND_URL`                | FastAPI backend base URL — used for the `/practice` page and on `/integrations`. |

## Build

```bash
npm run build
npm start
```

## Deploy to Vercel

Connect the repo, point Vercel at this `dashboard/` directory as the project root, and set the
four env vars above. The same Supabase project is shared with the backend.

## Routes

- `/` — overview, bot toggle, recent activity
- `/conversations` — full list, search + status filter, unread handoffs sorted to top
- `/conversations/[id]` — conversation detail, take over / resume, handoff banner
- `/practice` — sandbox chat against the real prompt; sessions stored under `platform='practice'`
- `/corrections` — list + add + delete
- `/training` — list + add + delete
- `/integrations` — env-driven status of Anthropic / Instagram / ManyChat / Supabase / Booking
- `/about` — explains the bot's design
- `/login` — password gate

## API routes

Server-side handlers under `app/api/` — all hit Supabase via the service-role key:

- `auth/login`, `auth/logout`
- `corrections`, `training` — POST add, DELETE remove
- `toggle` — flips `bot_settings.instagram_enabled`
- `takeover`, `resume` — flip conversation status
- `handoff/seen` — marks `metadata.handoff.seen = true`
- `practice` — proxies to `BACKEND_URL/practice/chat` and `/practice/reset`
