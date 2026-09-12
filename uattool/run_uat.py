#!/usr/bin/env python3
"""Master runner for the UAT tool.

Usage:
  python run_uat.py                       # everything except money-tier + manual rows
  python run_uat.py --only 01,01b,02       # just these catalog rows
  python run_uat.py --confirm-money        # also run rows 90/91 (real Stripe + Interac charges)

Target is always kdc.minipass.me (override with UAT_BASE_URL env var). See
CATALOG.md for the full row-by-row description of what each script does.

Runs headed by default — a real Chrome window pops up for each row so you can
watch it happen — and prints live pass/fail progress per row as it runs, not
just a final tally.
"""

import argparse
import sys

from lib import catalog, report
from lib.runner import run_all


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", help="Comma-separated catalog row numbers to run, e.g. 01,01b,02")
    parser.add_argument(
        "--confirm-money", action="store_true",
        help="Also run rows 90/91, which move real money. Requires you to be present to enter a real "
             "card number / confirm a real e-transfer when prompted.",
    )
    args = parser.parse_args()

    only = set(args.only.split(",")) if args.only else None

    results, manual_reminders, run_id = run_all(only=only, money_confirmed=args.confirm_money)

    run_timestamp = run_id
    report_path = report.write_report(results, run_timestamp, manual_reminders)

    status_by_order = {r["order"]: r["status"] for r in results}
    catalog.save_last_status(status_by_order, run_timestamp, report_path)
    catalog_path = catalog.write_catalog_md(status_by_order=status_by_order, run_timestamp=run_timestamp)

    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    skipped = sum(1 for r in results if r["status"] == "skipped")

    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    print(f"Report:  {report_path}")
    print(f"Catalog: {catalog_path}")

    if manual_reminders:
        print("\nStill owed (manual only):")
        for reminder in manual_reminders:
            print(f"  - {reminder}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
