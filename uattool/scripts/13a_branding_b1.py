"""Row 13a — branding fallback matrix case B1."""

from lib.branding_matrix import run_branding_case


def run(ctx):
    run_branding_case(
        ctx, case_id="B1", org_logo=True, activity_logo=True, cover_photo=True
    )
