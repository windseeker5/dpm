"""Row 13f — branding fallback matrix case B6."""

from lib.branding_matrix import run_branding_case


def run(ctx):
    run_branding_case(
        ctx, case_id="B6", org_logo=False, activity_logo=True, cover_photo=False
    )
