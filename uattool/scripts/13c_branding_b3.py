"""Row 13c — branding fallback matrix case B3."""

from lib.branding_matrix import run_branding_case


def run(ctx):
    run_branding_case(
        ctx, case_id="B3", org_logo=True, activity_logo=False, cover_photo=True
    )
