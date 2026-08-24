# Citation Radar project plan

## Goal
Notify the user when any tracked publication by a selected researcher receives a newly indexed citation.

## v0.1 MVP
1. Resolve researcher to OpenAlex author ID.
2. Sync the author's publications.
3. Query citing works for every tracked publication.
4. Store work/citation IDs in SQLite.
5. On first run, baseline silently.
6. On later runs, notify only newly observed citing works via Telegram.
7. Run manually or from cron/GitHub Actions.

## v0.2
- Add Semantic Scholar as a second citation source.
- Normalize/deduplicate the same citing work across sources by DOI, then title fingerprint.
- Add Discord webhook notifier.
- Add retry/backoff and structured logging.
- Add `doctor` command for config diagnostics.

## v0.3
- Optional email notifier.
- Daily digest mode versus instant notification mode.
- Small web dashboard showing tracked works and citation timeline.
- Abstract-based AI summary of why the citing paper appears to cite the tracked paper, when citation context/full text is legally available.

## Google Scholar / ResearchGate strategy
Do not scrape these sites in the MVP. Use them as manual verification surfaces. If later required, investigate compliant third-party APIs/search providers rather than brittle direct scraping.

## Acceptance criteria for v0.1
- Re-running `check` never repeats the same citation notification.
- First baseline run sends zero notifications.
- A newly returned OpenAlex citing-work ID produces exactly one Telegram message.
- Missing Telegram credentials fail clearly rather than silently.
