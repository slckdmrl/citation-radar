# Citation Radar

Citation Radar watches an author's works in OpenAlex, stores known citing works in SQLite, and sends a Telegram message only when a new citation appears after the initial baseline.

## MVP scope

- OpenAlex author discovery by name
- Import all works for one OpenAlex author
- Fetch citing works for each tracked work
- SQLite baseline + deduplication
- Telegram notifications for newly discovered citations
- Safe first run: existing citations are stored but not notified

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
```

`citation-radar` requires Python 3.11 or newer. On machines where `python3` still points to 3.9 or 3.10, use a 3.11+ interpreter explicitly as shown above.

Then edit `.env`:

- Set `OPENALEX_API_KEY` if you have one. As of August 24, 2026, current OpenAlex docs describe API keys as the supported request identifier. The app still accepts `OPENALEX_EMAIL` as an optional contact field.
- Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.
- Leave `OPENALEX_AUTHOR_ID` empty until you discover the correct author.
- `DATABASE_PATH=./citation_radar.db` is resolved relative to the `.env` file, so the same database is used even if you run commands from another working directory.

Discover the author first:

```bash
citation-radar discover-author "Jane Doe"
```

Copy the chosen OpenAlex author ID into `.env` as `OPENALEX_AUTHOR_ID`, then run:

```bash
citation-radar check --baseline
citation-radar check
```

For the first real run, use `--baseline`. Afterwards run `citation-radar check` from cron, GitHub Actions, or a small server.

If you do not want to edit `.env` yet, you can also import works once with:

```bash
citation-radar sync-author --author-id A1234567890
```

## Run on GitHub Actions

If you want citation checks to continue while your computer is off, use the included GitHub Actions workflow in `.github/workflows/citation-radar.yml`.

What it does:

- Runs automatically every 6 hours.
- Supports manual runs from the Actions tab.
- Automatically uses `--baseline` on the first remote run when no saved SQLite database exists yet.
- Saves `citation_radar.db` to a dedicated `citation-radar-state` branch so deduplication and notification history survive between runs.

Repository setup:

1. Push this repository to GitHub.
2. In GitHub, open `Settings -> Secrets and variables -> Actions`.
3. Add these repository secrets:
   - `OPENALEX_AUTHOR_ID`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `OPENALEX_EMAIL` (optional)
   - `OPENALEX_API_KEY` (optional, recommended if you have one)
4. Open the `Actions` tab and run the `Citation Radar` workflow once.
5. For the first manual run, set the `baseline` input to `true` if you want to force a fresh baseline.

Notes:

- The workflow persists state in a separate Git branch named `citation-radar-state`. It will create that branch automatically on the first successful run.
- If you ever want to reset the remote baseline, either delete the `citation-radar-state` branch or manually run the workflow with `baseline=true`.
- GitHub Actions uses repository secrets, not your local `.env` file.

## Telegram setup

Create a bot with BotFather, obtain the bot token, send your bot one message, then use the target chat ID as `TELEGRAM_CHAT_ID`.

## Design notes

Google Scholar and ResearchGate are intentionally not scraped in v0.1. Their pages are brittle for automation and may trigger anti-bot controls. OpenAlex is the primary structured citation source. Semantic Scholar can be added as a second source in v0.2.
