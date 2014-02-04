import logging
import hashlib
from functools import partial

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from edxmako.shortcuts import render_to_string

from xmodule_modifiers import replace_static_urls, wrap_xblock, wrap_fragment
from xmodule.error_module import ErrorDescriptor
from xmodule.exceptions import NotFoundError, ProcessingError
from xmodule.modulestore.django import modulestore, loc_mapper
from xmodule.modulestore.locator import Locator
from xmodule.x_module import ModuleSystem
from xblock.runtime import KvsFieldData
from xblock.django.request import webob_to_django_response, django_to_webob_request
from xblock.exceptions import NoSuchHandlerError
from xblock.fragment import Fragment

from lms.lib.xblock.field_data import LmsFieldData
from lms.lib.xblock.runtime import quote_slashes, unquote_slashes

from util.sandboxing import can_execute_unsafe_code

import static_replace
from .session_kv_store import SessionKeyValueStore
from .helpers import render_from_lms
from ..utils import get_course_for_item

from contentstore.views.access import get_user_role

__all__ = ['preview_handler']

log = logging.getLogger(__name__)


@login_required
def preview_handler(request, usage_id, handler, suffix=''):
    """
    Dispatch an AJAX action to an xblock

    usage_id: The usage-id of the block to dispatch to, passed through `quote_slashes`
    handler: The handler to execute
    suffix: The remainder of the url to be passed to the handler
    """
    # Note: usage_id is currently the string form of a Location, but in the
    # future it will be the string representation of a Locator.
    location = unquote_slashes(usage_id)

    descriptor = modulestore().get_item(location)
    context = {}
    instance = _load_preview_module(request, descriptor, context)
    # Let the module handle the AJAX
    req = django_to_webob_request(request)
    try:
        resp = instance.handle(handler, req, suffix)

    except NoSuchHandlerError:
        log.exception("XBlock %s attempted to access missing handler %r", instance, handler)
        raise Http404

    except NotFoundError:
        log.exception("Module indicating to user that request doesn't exist")
        raise Http404

    except ProcessingError:
        log.warning("Module raised an error while processing AJAX request",
                    exc_info=True)
        return HttpResponseBadRequest()

    except Exception:
        log.exception("error processing ajax call")
        raise

    return webob_to_django_response(resp)


class PreviewModuleSystem(ModuleSystem):  # pylint: disable=abstract-method
    """
    An XModule ModuleSystem for use in Studio previews
    """
    def handler_url(self, block, handler_name, suffix='', query='', thirdparty=False):
        return reverse('preview_handler', kwargs={
            'usage_id': quote_slashes(unicode(block.scope_ids.usage_id).encode('utf-8')),
            'handler': handler_name,
            'suffix': suffix,
        }) + '?' + query


def _preview_module_system(request, descriptor, context):
    """
    Returns a ModuleSystem for the specified descriptor that is specialized for
    rendering module previews.

    request: The active django request
    descriptor: An XModuleDescriptor
    """

    if isinstance(descriptor.location, Locator):
        course_location = loc_mapper().translate_locator_to_location(descriptor.location, get_course=True)
        course_id = course_location.course_id
    else:
        course_id = get_course_for_item(descriptor.location).location.course_id

    wrappers = [
        # This wrapper wraps the module in the template specified above
        partial(wrap_xblock, 'PreviewRuntime', display_name_only=descriptor.category == 'static_tab'),

        # This wrapper replaces urls in the output that start with /static
        # with the correct course-specific url for the static content
        partial(replace_static_urls, None, course_id=course_id),
    ]
    # In the container view only, add a new component wrapper
    if context.get('container_view', None):
        wrappers.append(_studio_wrap_xblock)

    return PreviewModuleSystem(
        static_url=settings.STATIC_URL,
        # TODO (cpennington): Do we want to track how instructors are using the preview problems?
        track_function=lambda event_type, event: None,
        filestore=descriptor.runtime.resources_fs,
        get_module=partial(_load_preview_module, request, context=context),
        render_template=render_from_lms,
        debug=True,
        replace_urls=partial(static_replace.replace_static_urls, data_directory=None, course_id=course_id),
        user=request.user,
        can_execute_unsafe_code=(lambda: can_execute_unsafe_code(course_id)),
        mixins=settings.XBLOCK_MIXINS,
        course_id=course_id,
        anonymous_student_id='student',

        # Set up functions to modify the fragment produced by student_view
        wrappers=wrappers,
        error_descriptor_class=ErrorDescriptor,
        # get_user_role accepts a location or a CourseLocator.
        # If descriptor.location is a CourseLocator, course_id is unused.
        get_user_role=lambda: get_user_role(request.user, descriptor.location, course_id),
    )


def _load_preview_module(request, descriptor, context):
    """
    Return a preview XModule instantiated from the supplied descriptor.

    request: The active django request
    descriptor: An XModuleDescriptor
    """
    student_data = KvsFieldData(SessionKeyValueStore(request))
    descriptor.bind_for_student(
        _preview_module_system(request, descriptor, context),
        LmsFieldData(descriptor._field_data, student_data),  # pylint: disable=protected-access
    )
    return descriptor


# pylint: disable=unused-argument
def _studio_wrap_xblock(xblock, view, frag, context, display_name_only=False):
    """
    Wraps the results of rendering an XBlock view in a div which adds a header and Studio action buttons.
    """
    template_context = {
        'xblock_context': context,
        'xblock': xblock,
        'content': xblock.display_name if display_name_only else frag.content,
    }
    if xblock.category == 'vertical':
        html = render_to_string('studio_vertical_wrapper.html', template_context)
    else:
        html = render_to_string('studio_xblock_wrapper.html', template_context)
    return wrap_fragment(frag, html)


def get_preview_fragment(request, descriptor, context):
    """
    Returns the HTML returned by the XModule's student_view,
    specified by the descriptor and idx.
    """
    module = _load_preview_module(request, descriptor, context)

    try:
        fragment = module.render("student_view", context)
    except Exception as exc:                          # pylint: disable=W0703
        log.debug("Unable to render student_view for %r", module, exc_info=True)
        fragment = Fragment(render_to_string('html_error.html', {'message': str(exc)}))
    return fragment
