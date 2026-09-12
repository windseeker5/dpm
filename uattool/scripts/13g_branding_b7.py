"""Row 13g — branding fallback matrix case B7."""

from lib.branding_matrix import run_branding_case


def run(ctx):
    run_branding_case(
        ctx, case_id="B7", org_logo=False, activity_logo=False, cover_photo=True
    )
