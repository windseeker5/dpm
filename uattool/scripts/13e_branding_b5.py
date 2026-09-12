"""Row 13e — branding fallback matrix case B5."""

from lib.branding_matrix import run_branding_case


def run(ctx):
    run_branding_case(
        ctx, case_id="B5", org_logo=False, activity_logo=True, cover_photo=True
    )
