"""
PageObjects related to the AcidBlock
"""

from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise, BrokenPromise, fulfill


class AcidView(PageObject):
    """
    A :class:`.PageObject` representing the rendered view of the :class:`.AcidBlock`.
    """
    url = None

    def __init__(self, browser, context_selector):
        """
        Args:
            browser (splinter.browser.Browser): The browser that this page is loaded in.
            context_selector (str): The selector that identifies where this :class:`.AcidBlock` view
                is on the page.
        """
        super(AcidView, self).__init__(browser)
        if isinstance(context_selector, unicode):
            context_selector = context_selector.encode('utf-8')
        self.context_selector = context_selector

    def is_browser_on_page(self):
        return (
            self.is_css_present('{} .acid-block'.format(self.context_selector)) and
            self.browser.evaluate_script("$({!r}).data('initialized')".format(self.context_selector))
        )

    def test_passed(self, test_selector):
        """
        Return whether a particular :class:`.AcidBlock` test passed.
        """
        selector = '{} .acid-block {} .pass'.format(self.context_selector, test_selector)
        return bool(self.q(css=selector).execute(try_interval=0.1, timeout=3))

    @property
    def init_fn_passed(self):
        """
        Whether the init-fn test passed in this view of the :class:`.AcidBlock`.
        """
        return self.test_passed('.js-init-run')

    @property
    def doc_ready_passed(self):
        """
        Whether the document-ready test passed in this view of the :class:`.AcidBlock`.
        """
        return self.test_passed('.document-ready-run')

    def scope_passed(self, scope):
        return all(
            self.test_passed('.scope-storage-test.scope-{} {}'.format(scope, test))
            for test in (
                ".server-storage-test-returned",
                ".server-storage-test-succeeded",
                ".client-storage-test-returned",
                ".client-storage-test-succeeded",
            )
        )

    def __repr__(self):
        return "{}(<browser>, {!r})".format(self.__class__.__name__, self.context_selector)
