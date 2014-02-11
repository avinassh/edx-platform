"""
This file implements the Microsite support for the Open edX platform.
A microsite enables the following features:

1) Mapping of sub-domain name to a 'brand', e.g. foo-university.edx.org
2) Present a landing page with a listing of courses that are specific to the 'brand'
3) Ability to swap out some branding elements in the website
"""
import threading
import os.path

from django.conf import settings

_microsite_configuration_threadlocal = threading.local()
_microsite_configuration_threadlocal.data = {}


class Microsite(object):
    """
    Class to handle all of the processing of Microsites
    """
    @classmethod
    def has_configuration_set(cls):
        """
        Returns whether there is any Microsite configuration settings
        """
        return getattr(settings, "MICROSITE_CONFIGURATION", False)

    @classmethod
    def get_configuration(cls):
        """
        Returns the current request's microsite configuration
        """
        if not hasattr(_microsite_configuration_threadlocal, 'data'):
            return {}

        return _microsite_configuration_threadlocal.data

    @classmethod
    def is_request_in_microsite(cls):
        """
        This will return if current request is a request within a microsite
        """
        return cls.get_configuration()

    @classmethod
    def get_value(cls, val_name, default=None):
        """
        Returns a value associated with the request's microsite, if present
        """
        configuration = cls.get_configuration()
        return configuration.get(val_name, default)

    @classmethod
    def get_template_path(cls, relative_path):
        """
        Returns a path to a Mako template, which can either be in
        a microsite directory (as an override) or will just return what is passed in
        """

        if not cls.is_request_in_microsite():
            return relative_path

        microsite_template_path = cls.get_value('template_dir')

        if microsite_template_path:
            search_path = microsite_template_path / relative_path

            if os.path.isfile(search_path):
                path = '{0}/templates/{1}'.format(
                    cls.get_value('microsite_name'),
                    relative_path
                )
                return path

        return relative_path

    @classmethod
    def get_value_for_org(cls, org, val_name, default=None):
        """
        This returns a configuration value for a microsite which has an org_filter that matches
        what is passed in
        """
        if not cls.has_configuration_set():
            return default

        for key in settings.MICROSITE_CONFIGURATION.keys():
            org_filter = settings.MICROSITE_CONFIGURATION[key].get('course_org_filter', None)
            if org_filter == org:
                return settings.MICROSITE_CONFIGURATION[key].get(val_name, default)
        return default

    @classmethod
    def get_all_orgs(cls):
        """
        This returns a set of orgs that are considered within a Microsite. This can be used,
        for example, to do filtering
        """
        org_filter_set = []
        if not cls.has_configuration_set():
            return org_filter_set

        for key in settings.MICROSITE_CONFIGURATION:
            org_filter = settings.MICROSITE_CONFIGURATION[key].get('course_org_filter')
            if org_filter:
                org_filter_set.append(org_filter)

        return org_filter_set

    @classmethod
    def clear(cls):
        """
        Clears out any microsite configuration from the current request/thread
        """
        _microsite_configuration_threadlocal.data = {}

    @classmethod
    def set_by_domain(cls, domain):
        if not cls.has_configuration_set():
            return

        if not domain:
            return

        for key in settings.MICROSITE_CONFIGURATION.keys():
            subdomain = settings.MICROSITE_CONFIGURATION[key]['domain_prefix']
            if domain.startswith(subdomain):
                config = settings.MICROSITE_CONFIGURATION[key].copy()
                config['subdomain'] = subdomain
                config['site_domain'] = domain
                _microsite_configuration_threadlocal.data = config
                return config

        return None

    @classmethod
    def match_university(cls, domain):
        """
        LEGACY SUPPORT: Return the university name specified for the domain, or None
        if no university was specified.
        Right now this seems to only support 'Edge' splash page
        """
        if not settings.FEATURES['SUBDOMAIN_BRANDING'] or domain is None:
            return None

        subdomain = cls.pick_subdomain(domain, settings.SUBDOMAIN_BRANDING.keys())
        return settings.SUBDOMAIN_BRANDING.get(subdomain)

    @classmethod
    def pick_subdomain(cls, domain, options, default='default'):
        """
        LEGACY SUPPORT: Attempt to match the incoming request's HOST domain with a configuration map
        to see what subdomains are supported in Microsites.
        Right now this seems to only support 'Edge' splash page
        """
        for option in options:
            if domain.startswith(option):
                return option
        return default
