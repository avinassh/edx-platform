"""
This is a localdev test for the Microsite processing pipeline
"""
# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0614

from .dev import *


MICROSITE_CONFIGURATION = {
    "openedx": {
        "domain_prefix": "openedx",
        "university": "openedx",
        "platform_name": "Open edX",
        "logo_image_url": "openedx/images/header-logo.png",
        "email_from_address": "openedx@edx.org",
        "payment_support_email": "openedx@edx.org",
        "ENABLE_MKTG_SITE": False,
        "SITE_NAME": "openedx.localhost",
        "course_org_filter": "CDX",
        "course_about_show_social_links": False,
        "css_overrides_file": "openedx/css/openedx.css",
        "show_partners": False,
        "show_homepage_promo_video": False,
        "course_index_overlay_text": "Explore free courses from leading universities.",
        "course_index_overlay_logo_file": "openedx/images/header-logo.png",
        "homepage_overlay_html": "<h1>Take an Open edX Course</h1>"
    },
    "ethicon": {
        "domain_prefix":"ethicon",
        "university":"ethicon",
        "platform_name": "Ethicon on edX",
        "logo_image_url": "ethicon/images/ce_rgb_logo-1.png",
        "show_only_org_on_student_dashboard": True,
        "email_from_address": "ethicon@ethicon.com",
        "payment_support_email": "ethicon@ethicon.com",
        "ENABLE_MKTG_SITE":  False,
        "SITE_NAME": "ethicon.localhost",
        "course_org_filter": "EthiconX",
        "course_about_show_social_links": False,
        "css_overrides_file": "ethicon/css/ethicon.css",
        "show_partners": False,
        "show_homepage_promo_video": True,
        "homepage_promo_video_youtube_id": "RsRRMVzSXmE",
        "course_index_overlay_text": "<img src='/static/ethicon/images/Ethicon_Better_Surgery_Vertical.png' width='400' height='103' />",
        "homepage_overlay_html": "<img src='/static/ethicon/images/Ethicon_Better_Surgery_Vertical.png'  width='400' height='103' />",
        "favicon_path": "ethicon/images/Ethicon_Spectrum_Red_Logo.ico"
    }
}

MICROSITE_ROOT_DIR = ENV_ROOT / 'edx-microsite'

# pretend we are behind some marketing site, we want to be able to assert that the Microsite config values override
# this global setting
FEATURES['ENABLE_MKTG_SITE'] = True
FEATURES['USE_MICROSITES'] = True
