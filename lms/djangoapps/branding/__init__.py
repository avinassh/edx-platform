from xmodule.modulestore.django import modulestore
from xmodule.course_module import CourseDescriptor
from django.conf import settings

from microsite_configuration.microsite import Microsite


def get_visible_courses():
    """
    Return the set of CourseDescriptors that should be visible in this branded instance
    """
    _courses = modulestore().get_courses()

    courses = [c for c in _courses
               if isinstance(c, CourseDescriptor)]
    courses = sorted(courses, key=lambda course: course.number)

    subdomain = Microsite.get_value('subdomain')

    # See if we have filtered course listings in this domain
    filtered_visible_ids = None

    # this is legacy format which is outside of the microsite feature
    if hasattr(settings, 'COURSE_LISTINGS') and subdomain in settings.COURSE_LISTINGS:
        filtered_visible_ids = frozenset(settings.COURSE_LISTINGS[subdomain])

    filtered_by_org = Microsite.get_value('course_org_filter')

    if filtered_by_org:
        return [course for course in courses if course.location.org == filtered_by_org]
    if filtered_visible_ids:
        return [course for course in courses if course.id in filtered_visible_ids]
    else:
        # Let's filter out any courses in an "org" that has been declared to be
        # in a Microsite
        org_filter_out_set = Microsite.get_all_orgs()
        return [course for course in courses if course.location.org not in org_filter_out_set]


def get_university_for_request():
    """
    Return the university name specified for the domain, or None
    if no university was specified
    """
    return Microsite.get_value('university')


def get_logo_url():
    """
    Return the url for the branded logo image to be used
    """

    # if the MicrositeConfiguration has a value for the logo_image_url
    # let's use that
    image_url = Microsite.get_value('logo_image_url')
    if image_url:
        return '{static_url}{image_url}'.format(
            static_url=settings.STATIC_URL,
            image_url=image_url
        )

    # otherwise, use the legacy means to configure this
    university = Microsite.get_value('university')

    if university is None:
        return '{static_url}images/header-logo.png'.format(
            static_url=settings.STATIC_URL
        )

    return '{static_url}images/{uni}-on-edx-logo.png'.format(
        static_url=settings.STATIC_URL, uni=university
    )
