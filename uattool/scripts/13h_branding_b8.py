"""Row 13h — branding fallback matrix case B8."""

from lib.branding_matrix import run_branding_case


def run(ctx):
    run_branding_case(
        ctx, case_id="B8", org_logo=False, activity_logo=False, cover_photo=False
    )
