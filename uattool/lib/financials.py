"""Read and assert on the financial report figures.

Two independent readings, deliberately:

  read_tiles()      the KPI tiles on /reports/financial — these come from
                    monthly_financial_summary (utils.py:5761)
  read_csv_totals() the /reports/financial/export CSV, summed per bucket — this comes from
                    monthly_transactions_detail (utils.py:5598)

Those are two different SQL views, and they have disagreed in the past: before task55 the
summary view dropped unpaid passports whose activity had no other transaction that month, so
the two differed by $100 on the real tenant while both looked individually plausible.
assert_views_agree() is what catches that class of bug, so call it on every reading.

Everything here asserts DELTAS, never absolute totals — the live tenant holds real money and
its starting figures are unknowable. Read, act, read again, compare the difference.
"""

import csv
import io

from . import config

# The five tiles rendered on /reports/financial, keyed by the label text above each value.
# The page renders each tile TWICE — the mobile carousel first (whole dollars, {:,.0f}) then the
# desktop row (cents, {:,.2f}) — so the reader below picks the one with cents. Do not try to
# scope this by container: `.d-none.d-md-block` matches an earlier element on the page.
TILE_LABELS = {
    "cash_received": "CASH RECEIVED",
    "cash_paid": "CASH PAID",
    "net_cash_flow": "NET CASH FLOW",
    "accounts_receivable": "ACCOUNTS RECEIVABLE (AR)",
    "accounts_payable": "ACCOUNTS PAYABLE (AP)",
}

_READ_TILES_JS = """
(labels) => {
  const out = {};
  for (const [key, label] of Object.entries(labels)) {
    const candidates = [];
    for (const body of document.querySelectorAll('.card-body')) {
      const caption = body.querySelector('.text-uppercase');
      if (!caption || caption.innerText.trim().toUpperCase() !== label) continue;
      const value = body.querySelector('.h1, .h2');
      if (value) candidates.push(value.innerText.trim());
    }
    // Desktop tile carries cents, the mobile one does not. Prefer cents.
    out[key] = candidates.find(t => t.includes('.')) ?? candidates[0] ?? null;
  }
  return out;
}
"""


def _parse_money(text, field, url):
    if text is None:
        raise AssertionError(
            f"Could not find the {field!r} tile on {url}. The report markup may have changed — "
            f"expected a .card-body whose .text-uppercase caption reads "
            f"{TILE_LABELS[field]!r} with a .h1/.h2 value beside it."
        )
    cleaned = text.replace("$", "").replace(",", "").replace("−", "-").strip()
    # Negative figures may render as ($12.34)
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
    try:
        return float(cleaned)
    except ValueError:
        raise AssertionError(f"Could not parse the {field!r} tile value {text!r} on {url} as money.")


def read_tiles(page, base_url=None, period="all"):
    """The five KPI tiles from /reports/financial, as floats. Sourced from the summary view."""
    base_url = base_url or config.BASE_URL
    url = f"{base_url}/reports/financial?period={period}"
    page.goto(url)
    page.wait_for_load_state("networkidle", timeout=20000)

    raw = page.evaluate(_READ_TILES_JS, TILE_LABELS)
    return {field: _parse_money(raw.get(field), field, url) for field in TILE_LABELS}


def fetch_csv_rows(page, base_url=None, period="all"):
    """The financial export as a list of dicts. Fetched in-page so it uses the logged-in session."""
    base_url = base_url or config.BASE_URL
    url = f"{base_url}/reports/financial/export?format=csv&period={period}"

    result = page.evaluate(
        """
        async (u) => {
          const r = await fetch(u, { credentials: 'same-origin' });
          return { status: r.status, body: await r.text() };
        }
        """,
        url,
    )
    if result["status"] != 200:
        raise AssertionError(f"Financial CSV export returned HTTP {result['status']} for {url}")

    rows = list(csv.DictReader(io.StringIO(result["body"])))
    if not rows:
        raise AssertionError(f"Financial CSV export at {url} had a header but no data rows.")
    return rows


def read_csv_totals(page, base_url=None, period="all"):
    """Same four money buckets, recomputed from the export. Sourced from the detail view.

    payment_status in the detail view is one of 'Paid', 'Unpaid (AR)', 'Unpaid (AP)'.
    """
    rows = fetch_csv_rows(page, base_url=base_url, period=period)

    totals = {"cash_received": 0.0, "cash_paid": 0.0,
              "accounts_receivable": 0.0, "accounts_payable": 0.0}

    for row in rows:
        try:
            amount = float((row.get("amount") or "0").replace("$", "").replace(",", ""))
        except ValueError:
            continue
        kind = (row.get("transaction_type") or "").strip()
        status = (row.get("payment_status") or "").strip()

        if kind == "Income":
            if status == "Paid":
                totals["cash_received"] += amount
            else:
                totals["accounts_receivable"] += amount
        elif kind == "Expense":
            if status == "Paid":
                totals["cash_paid"] += amount
            else:
                totals["accounts_payable"] += amount

    return {k: round(v, 2) for k, v in totals.items()}


def assert_views_agree(tiles, csv_totals, ctx, label, tolerance=0.01):
    """The summary view and the detail view must report the same money.

    This is the invariant that caught the pre-task55 receivables bug. Expenses are compared too,
    though only the revenue side has ever drifted.
    """
    problems = []
    for field in ("cash_received", "accounts_receivable", "cash_paid", "accounts_payable"):
        a, b = tiles[field], csv_totals[field]
        if abs(a - b) > tolerance:
            problems.append(f"{field}: report page says ${a:,.2f}, CSV export says ${b:,.2f} (off by ${a - b:,.2f})")

    if problems:
        raise AssertionError(
            f"[{label}] The financial report and the CSV export disagree, which means the summary "
            f"view and the detail view are out of sync:\n  " + "\n  ".join(problems)
        )
    ctx.note(f"[{label}] Report page and CSV export agree on every bucket (summary view == detail view).")


def assert_delta(before, after, expected, ctx, label, tolerance=0.01):
    """Assert each field moved by exactly the expected amount.

    Any field NOT named in `expected` must not have moved at all. That is what catches
    double-counting: a bucket transfer that also inflates a total shows up here.
    """
    problems = []
    for field in before:
        actual = round(after[field] - before[field], 2)
        want = round(float(expected.get(field, 0.0)), 2)
        if abs(actual - want) > tolerance:
            problems.append(
                f"{field}: expected to move by ${want:+,.2f}, actually moved ${actual:+,.2f} "
                f"(${before[field]:,.2f} -> ${after[field]:,.2f})"
            )

    if problems:
        raise AssertionError(f"[{label}] Financial report did not move as expected:\n  " + "\n  ".join(problems))

    moved = ", ".join(f"{f} {float(v):+,.2f}" for f, v in expected.items() if float(v)) or "nothing"
    ctx.note(f"[{label}] Financial report moved exactly as expected ({moved}); every other bucket unchanged.")


def assert_csv_line(page, ctx, needle, expected_amount, base_url=None, period="all"):
    """Assert the export contains a row mentioning `needle` for `expected_amount`."""
    rows = fetch_csv_rows(page, base_url=base_url, period=period)
    needle_lc = str(needle).lower()

    for row in rows:
        blob = " ".join(str(v) for v in row.values()).lower()
        if needle_lc in blob:
            try:
                amount = float((row.get("amount") or "0").replace("$", "").replace(",", ""))
            except ValueError:
                amount = None
            if amount is not None and abs(amount - float(expected_amount)) <= 0.01:
                ctx.note(
                    f"CSV export contains {needle!r} at ${float(expected_amount):,.2f} "
                    f"(project={row.get('project')!r}, memo={row.get('memo')!r})."
                )
                return row
            raise AssertionError(
                f"CSV export has a row for {needle!r} but the amount is {amount}, "
                f"expected {float(expected_amount):,.2f}. Row: {row!r}"
            )

    raise AssertionError(
        f"CSV export has no row mentioning {needle!r}. "
        f"{len(rows)} row(s) checked — the sale may not have reached monthly_transactions_detail."
    )


def assert_report_line(page, ctx, needle, expected_amount, base_url=None, period="all"):
    """Assert the /reports/financial page itself shows a transaction row for `needle`."""
    base_url = base_url or config.BASE_URL
    url = f"{base_url}/reports/financial?period={period}"
    page.goto(url)
    page.wait_for_load_state("networkidle", timeout=20000)

    amount_text = f"{float(expected_amount):,.2f}"
    # textContent, not innerText: per-activity transaction tables are inside collapsible
    # sections, and innerText returns "" for anything not currently visible.
    matches = page.evaluate(
        """
        ([needle, amount]) => [...document.querySelectorAll('tr')]
          .map(tr => tr.textContent.replace(/\\s+/g, ' ').trim())
          .filter(t => t.toLowerCase().includes(needle.toLowerCase()) && t.includes(amount))
        """,
        [str(needle), amount_text],
    )
    if not matches:
        raise AssertionError(
            f"No row on {url} mentions {needle!r} with ${amount_text}. "
            f"The sale is missing from the financial report page."
        )
    ctx.note(f"Financial report page shows {needle!r} at ${amount_text}: {matches[0][:160]!r}")
    return matches[0]


_ACTIVITY_ROW_JS = """
(name) => {
  const want = name.toLowerCase();
  for (const tr of document.querySelectorAll('tr')) {
    const cells = [...tr.querySelectorAll('td')];
    // The activity summary row is: name, cash received, cash paid, net, actions. The nested
    // per-activity transaction tables produce far wider rows, so the width check skips them.
    if (cells.length < 4 || cells.length > 5) continue;
    const first = cells[0].textContent.replace(/\\s+/g, ' ').trim();
    const lc = first.toLowerCase();
    // An activity with a cover image renders just its name. One falling back to a placeholder
    // letter avatar renders "<letter> <name>" in the same cell — 'Boutique' always does, since
    // it is a label inside the view and has no image. The length guard stops a short name from
    // matching the tail of a longer one.
    if (lc === want || (lc.endsWith(' ' + want) && first.length - name.length <= 3)) {
      return cells[1] ? cells[1].textContent.replace(/\\s+/g, ' ').trim() : null;
    }
  }
  return null;
}
"""


def activity_row_total(page, activity_name, base_url=None, period="all"):
    """CASH RECEIVED for one row of the 'Transactions by Activity' table, or None if absent.

    Pass "Boutique" to prove product money lands there, or a real activity name to prove it
    did not leak in. Pass "TOTAL" for the table's own total row.
    """
    base_url = base_url or config.BASE_URL
    page.goto(f"{base_url}/reports/financial?period={period}")
    page.wait_for_load_state("networkidle", timeout=20000)

    text = page.evaluate(_ACTIVITY_ROW_JS, activity_name)
    if text is None:
        return None
    return _parse_money(text, "cash_received", f"{base_url}/reports/financial (row {activity_name!r})")
