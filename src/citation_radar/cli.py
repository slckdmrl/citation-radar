from __future__ import annotations

import argparse
import sys

from .config import load_settings
from .db import Database
from .notifier import TelegramNotifier
from .openalex import OpenAlexClient
from .service import check_citations, sync_author_works


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="citation-radar")
    sub = parser.add_subparsers(dest="command", required=True)

    discover = sub.add_parser("discover-author", help="Search OpenAlex authors by name")
    discover.add_argument("name")

    sync = sub.add_parser("sync-author", help="Import/update works for configured author")
    sync.add_argument("--author-id", default=None)

    check = sub.add_parser("check", help="Check tracked works for new citations")
    check.add_argument("--baseline", action="store_true", help="Store existing citations without notifying")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    settings = load_settings()
    client = OpenAlexClient(settings.openalex_email)

    try:
        if args.command == "discover-author":
            for item in client.search_authors(args.name):
                author_id = item.get("id", "").rsplit("/", 1)[-1]
                name = item.get("display_name", "?")
                works = item.get("works_count", 0)
                cited = item.get("cited_by_count", 0)
                inst = ((item.get("last_known_institutions") or [{}])[0]).get("display_name", "")
                print(f"{author_id}\t{name}\tworks={works}\tcitations={cited}\t{inst}")
            return 0

        db = Database(settings.database_path)
        try:
            if args.command == "sync-author":
                author_id = args.author_id or settings.openalex_author_id
                if not author_id:
                    print("OPENALEX_AUTHOR_ID is missing. Use discover-author first.", file=sys.stderr)
                    return 2
                count = sync_author_works(db, client, author_id)
                print(f"Synced {count} works for {author_id}.")
                return 0

            if args.command == "check":
                author_id = settings.openalex_author_id
                if author_id:
                    sync_author_works(db, client, author_id)

                notifier = None
                if not args.baseline:
                    if not settings.telegram_bot_token or not settings.telegram_chat_id:
                        print("Telegram credentials missing. Use --baseline or configure Telegram.", file=sys.stderr)
                        return 2
                    notifier = TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id)

                result = check_citations(db, client, notifier, baseline=args.baseline)
                print(
                    f"Checked {result.works_checked} works; saw {result.citations_seen} citations; "
                    f"new={result.new_citations}; notified={result.notifications_sent}."
                )
                return 0
        finally:
            db.close()
    finally:
        client.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
