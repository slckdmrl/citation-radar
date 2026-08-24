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
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
```

Fill `.env`, then:

```bash
citation-radar discover-author "Jane Doe"
citation-radar check --baseline
citation-radar check
```

For the first real run, use `--baseline`. Afterwards run `citation-radar check` from cron, GitHub Actions, or a small server.

## Telegram setup

Create a bot with BotFather, obtain the bot token, send your bot one message, then use the target chat ID as `TELEGRAM_CHAT_ID`.

## Design notes

Google Scholar and ResearchGate are intentionally not scraped in v0.1. Their pages are brittle for automation and may trigger anti-bot controls. OpenAlex is the primary structured citation source. Semantic Scholar can be added as a second source in v0.2.
