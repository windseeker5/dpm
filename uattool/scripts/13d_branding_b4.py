"""Row 13d — branding fallback matrix case B4."""

from lib.branding_matrix import run_branding_case


def run(ctx):
    run_branding_case(
        ctx, case_id="B4", org_logo=True, activity_logo=False, cover_photo=False
    )
