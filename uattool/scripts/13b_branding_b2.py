"""Row 13b — branding fallback matrix case B2."""

from lib.branding_matrix import run_branding_case


def run(ctx):
    run_branding_case(
        ctx, case_id="B2", org_logo=True, activity_logo=True, cover_photo=False
    )
