"""
Module for code that should run during LMS startup
"""

from django.conf import settings

# Force settings to run so that the python path is modified
settings.INSTALLED_APPS  # pylint: disable=W0104

from django_startup import autostartup
import edxmako
import os


def run():
    """
    Executed during django startup
    """
    autostartup()

    if settings.FEATURES.get('USE_CUSTOM_THEME', False):
        enable_theme()

    if settings.FEATURES.get('USE_MICROSITES', False):
        enable_microsites()


def enable_theme():
    """
    Enable the settings for a custom theme, whose files should be stored
    in ENV_ROOT/themes/THEME_NAME (e.g., edx_all/themes/stanford).
    """
    # Workaround for setting THEME_NAME to an empty
    # string which is the default due to this ansible
    # bug: https://github.com/ansible/ansible/issues/4812
    if settings.THEME_NAME == "":
        settings.THEME_NAME = None
        return

    assert settings.FEATURES['USE_CUSTOM_THEME']
    settings.FAVICON_PATH = 'themes/{name}/images/favicon.ico'.format(
        name=settings.THEME_NAME
    )

    # Calculate the location of the theme's files
    theme_root = settings.ENV_ROOT / "themes" / settings.THEME_NAME

    # Include the theme's templates in the template search paths
    settings.TEMPLATE_DIRS.insert(0, theme_root / 'templates')
    settings.MAKO_TEMPLATES['main'].insert(0, theme_root / 'templates')
    edxmako.startup.run()

    # Namespace the theme's static files to 'themes/<theme_name>' to
    # avoid collisions with default edX static files
    settings.STATICFILES_DIRS.append(
        (u'themes/{}'.format(settings.THEME_NAME), theme_root / 'static')
    )


def enable_microsites():
    """
    Enable the use of microsites, which are websites that allow
    for subdomains for the edX platform, e.g. foo.edx.org
    """

    microsites_root = settings.MICROSITE_ROOT_DIR
    microsite_config_dict = settings.MICROSITE_CONFIGURATION

    for microsite_name in microsite_config_dict.keys():
        # Calculate the location of the microsite's files
        microsite_root = microsites_root / microsite_name
        microsite_config = microsite_config_dict[microsite_name]

        # pull in configuration information from each
        # microsite root

        if os.path.isdir(microsite_root):
            # store the path on disk for later use
            microsite_config['microsite_root'] = microsite_root

            template_dir = microsite_root / 'templates'
            microsite_config['template_dir'] = template_dir

            microsite_config['microsite_name'] = microsite_name
            print '**** Loading microsite {0}'.format(microsite_root)
        else:
            # not sure if we have application logging at this stage of
            # startup
            print '**** Error loading microsite {0}. Directory does not exist'.format(microsite_root)
            # remove from our configuration as it is not valid
            del microsite_config_dict[microsite_name]

    # if we have microsites, then let's turn on SUBDOMAIN_BRANDING
    # Note check size of the dict because some microsites might not be found on disk and
    # we could be left with none
    if microsite_config_dict:
        settings.FEATURES['SUBDOMAIN_BRANDING'] = True

        settings.TEMPLATE_DIRS.append(microsites_root)
        settings.MAKO_TEMPLATES['main'].append(microsites_root)
        edxmako.startup.run()

        settings.STATICFILES_DIRS.insert(0, microsites_root)
