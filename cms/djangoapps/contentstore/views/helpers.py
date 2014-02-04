from django.http import HttpResponse
from django.shortcuts import redirect
from edxmako.shortcuts import render_to_string, render_to_response
from xmodule.modulestore.django import loc_mapper, modulestore

__all__ = ['edge', 'event', 'landing']


# points to the temporary course landing page with log in and sign up
def landing(request, org, course, coursename):
    return render_to_response('temp-course-landing.html', {})


# points to the temporary edge page
def edge(request):
    return redirect('/')


def event(request):
    '''
    A noop to swallow the analytics call so that cms methods don't spook and poor developers looking at
    console logs don't get distracted :-)
    '''
    return HttpResponse(status=204)


def render_from_lms(template_name, dictionary, context=None, namespace='main'):
    """
    Render a template using the LMS MAKO_TEMPLATES
    """
    return render_to_string(template_name, dictionary, context, namespace="lms." + namespace)


def _xmodule_recurse(item, action):
    for child in item.get_children():
        _xmodule_recurse(child, action)

    action(item)


def xblock_studio_url(xblock):
    """
    Returns the Studio editing URL for the specified xblock.
    """
    category = xblock.category
    locator = loc_mapper().translate_location(None, xblock.location)
    old_location = loc_mapper().translate_locator_to_location(locator)
    parent_locators = modulestore().get_parent_locations(old_location, None)
    parent_xblock = modulestore().get_item(parent_locators[0])
    parent_category = parent_xblock.category
    if category == 'course':
        prefix = 'course'
    elif category == 'vertical' and parent_category == 'sequential':
        prefix = 'unit'     # only show the unit page for verticals directly beneath a subsection
    elif not xblock.has_children or category == 'sequential':
        prefix = None   # there is no page for this xblock
    else:
        prefix = 'container'
    if not prefix:
        return None
    return locator.url_reverse(prefix + '/', '')
