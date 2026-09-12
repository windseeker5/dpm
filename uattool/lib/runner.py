"""Discovers and executes scripts/*.py in catalog order, collects results."""

import importlib.util
import os
import time
import traceback

from . import config
from .catalog_data import CATALOG

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")


class Context:
    """Passed to every script's run(ctx). Carries config + report-writing helpers."""

    def __init__(self, order, script_name, money_confirmed, run_id):
        self.order = order
        self.script_name = script_name
        self.base_url = config.BASE_URL
        self.money_confirmed = money_confirmed
        self._notes = []
        self._screenshots = []
        # Keep every run's visual evidence. The old stable directory was overwritten by
        # later runs, leaving historical Markdown reports pointing at changed screenshots.
        self._shot_dir = os.path.join(
            config.SCREENSHOTS_DIR, run_id, f"{order}_{os.path.splitext(script_name)[0]}"
        )

    def note(self, message):
        self._notes.append(message)

    def screenshot(self, page, label):
        os.makedirs(self._shot_dir, exist_ok=True)
        filename = f"{label}.png"
        full_path = os.path.join(self._shot_dir, filename)
        page.screenshot(path=full_path, full_page=True)
        rel_path = os.path.relpath(full_path, config.REPORTS_DIR)
        self._screenshots.append(rel_path)
        return full_path


def _load_script_module(script_path):
    spec = importlib.util.spec_from_file_location(
        os.path.splitext(os.path.basename(script_path))[0], script_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_all(only=None, money_confirmed=False):
    """Run every non-manual catalog row in order (optionally filtered to `only`
    order values). Returns (results, manual_reminders).
    """
    results = []
    manual_reminders = []
    run_id = time.strftime("%Y-%m-%d_%H%M%S")

    for row in CATALOG:
        if row["manual"]:
            manual_reminders.append(f"[{row['order']}] {row['area']}: {row['description']}")
            continue

        if only and row["order"] not in only:
            continue

        script_path = os.path.join(SCRIPTS_DIR, row["script"])
        result = dict(
            order=row["order"], script=row["script"], area=row["area"],
            status="skipped", duration_s=0.0, error=None, screenshots=[], notes=[],
        )

        if row["money"] and not money_confirmed:
            result["status"] = "skipped"
            result["notes"].append("Skipped: money-moving step requires --confirm-money.")
            print(f"[{row['order']}] {row['area']} ... SKIPPED (requires --confirm-money)")
            results.append(result)
            continue

        if not os.path.exists(script_path):
            result["status"] = "skipped"
            result["notes"].append(f"Skipped: {row['script']} not implemented yet.")
            print(f"[{row['order']}] {row['area']} ... SKIPPED (not implemented yet)")
            results.append(result)
            continue

        print(f"[{row['order']}] {row['area']} ... running", flush=True)
        ctx = Context(row["order"], row["script"], money_confirmed, run_id)
        start = time.monotonic()
        try:
            module = _load_script_module(script_path)
            module.run(ctx)
            result["status"] = "pass"
        except Exception as exc:  # noqa: BLE001 - report every failure, don't stop the whole run
            result["status"] = "fail"
            result["error"] = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        finally:
            result["duration_s"] = time.monotonic() - start
            result["screenshots"] = ctx._screenshots
            result["notes"].extend(ctx._notes)

        duration = result["duration_s"]
        if result["status"] == "pass":
            print(f"[{row['order']}] {row['area']} ... PASS ({duration:.1f}s)")
        else:
            first_error_line = (result["error"] or "").strip().splitlines()[-1] if result["error"] else "unknown error"
            print(f"[{row['order']}] {row['area']} ... FAIL ({duration:.1f}s): {first_error_line}")

        results.append(result)

    return results, manual_reminders, run_id
