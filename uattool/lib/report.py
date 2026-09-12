"""Writes reports/report_<timestamp>.md from a run's results."""

import os
from datetime import datetime

from . import config


def write_report(results, run_timestamp, manual_reminders):
    """results: list of dicts with keys order, script, area, status, duration_s,
    error, screenshots (list of relative paths), notes (list of str).
    """
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    path = os.path.join(config.REPORTS_DIR, f"report_{run_timestamp}.md")

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    skipped = sum(1 for r in results if r["status"] == "skipped")

    lines = [
        f"# UAT Run Report — {run_timestamp}",
        "",
        f"Target: `{config.BASE_URL}`",
        "",
        f"**{passed}/{total} passed**, {failed} failed, {skipped} skipped.",
        "",
    ]

    for r in results:
        icon = {"pass": "✅", "fail": "❌", "skipped": "⏭️"}.get(r["status"], "?")
        lines.append(f"## {icon} [{r['order']}] {r['area']} — `{r['script']}`")
        lines.append(f"- Status: **{r['status']}**  ·  Duration: {r['duration_s']:.1f}s")
        if r.get("notes"):
            for note in r["notes"]:
                lines.append(f"- {note}")
        if r.get("screenshots"):
            for shot in r["screenshots"]:
                lines.append(f"- Screenshot: `{shot}`")
        if r["status"] == "fail" and r.get("error"):
            lines.append("")
            lines.append("```")
            lines.append(str(r["error"]))
            lines.append("```")
        lines.append("")

    lines.append("## Still owed — manual only")
    lines.append("")
    for reminder in manual_reminders:
        lines.append(f"- [ ] {reminder}")
    lines.append("")

    with open(path, "w") as f:
        f.write("\n".join(lines))

    return path


def now_timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")
