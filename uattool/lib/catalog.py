"""Generates CATALOG.md from catalog_data.py, optionally stamped with the
last run's per-row status.
"""

import json
import os

from . import config
from .catalog_data import CATALOG

STATUS_STATE_PATH = os.path.join(config.REPORTS_DIR, "last_status.json")
CATALOG_MD_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "CATALOG.md")

STATUS_ICON = {
    "pass": "✅ pass",
    "fail": "❌ fail",
    "skipped": "⏭️ skipped",
    "manual": "— manual",
    None: "—",
}


def load_last_status():
    if not os.path.exists(STATUS_STATE_PATH):
        return {}
    with open(STATUS_STATE_PATH) as f:
        return json.load(f)


def save_last_status(status_by_order, run_timestamp, report_path):
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    with open(STATUS_STATE_PATH, "w") as f:
        json.dump(
            {"run_timestamp": run_timestamp, "report_path": report_path, "status": status_by_order},
            f,
            indent=2,
        )


def render_catalog_md(status_by_order=None, run_timestamp=None):
    status_by_order = status_by_order or {}

    lines = [
        "# UAT Tool Catalog",
        "",
        "**Generated file — do not hand-edit the table.** To change a row, edit",
        "`lib/catalog_data.py` (and the matching script), then re-run",
        "`python run_uat.py` or `python -c \"from lib.catalog import write_catalog_md; write_catalog_md()\"`.",
        "",
        "Everything runs against `demo.minipass.me` as `kdresdell@gmail.com` (password via the",
        "`UAT_ADMIN_PASSWORD` env var — never hardcoded here, see lib/config.py)",
        "unless marked **[MANUAL]**. Rows 90/91 move real money and only run with `--confirm-money`.",
        "",
    ]

    if run_timestamp:
        lines.append(f"_Last run: {run_timestamp}_")
        lines.append("")

    lines.append(
        "| # | Script | Area | Description | Credentials | Email used | Viewport | Verifies | Last run |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|")

    for row in CATALOG:
        status_key = "manual" if row["manual"] else status_by_order.get(row["order"])
        status_label = STATUS_ICON.get(status_key, STATUS_ICON[None])
        script_label = row["script"] if row["script"] else "_(none — manual)_"
        money_prefix = "💰 " if row["money"] else ""
        lines.append(
            "| {order} | {script} | {money}{area} | {description} | {credentials} | {email} | {viewport} | {verifies} | {status} |".format(
                order=row["order"],
                script=script_label,
                money=money_prefix,
                area=row["area"],
                description=row["description"].replace("|", "\\|"),
                credentials=row["credentials"],
                email=row["email"],
                viewport=row["viewport"],
                verifies=row["verifies"].replace("|", "\\|"),
                status=status_label,
            )
        )

    return "\n".join(lines) + "\n"


def write_catalog_md(status_by_order=None, run_timestamp=None):
    content = render_catalog_md(status_by_order=status_by_order, run_timestamp=run_timestamp)
    with open(CATALOG_MD_PATH, "w") as f:
        f.write(content)
    return CATALOG_MD_PATH


if __name__ == "__main__":
    last = load_last_status()
    write_catalog_md(
        status_by_order=last.get("status"),
        run_timestamp=last.get("run_timestamp"),
    )
    print(f"Wrote {CATALOG_MD_PATH}")
