define(["jquery", "underscore", "js/views/baseview", "js/utils/handle_iframe_binding", "sinon", "js/spec/create_sinon"],
    function ($, _, BaseView, IframeBinding, sinon, create_sinon) {

        describe("BaseView", function() {
            var baseView,
                baseViewPrototype;

            describe("BaseView rendering", function () {
                var iframeBinding_spy;

                beforeEach(function () {
                    baseViewPrototype = BaseView.prototype;
                    iframeBinding_spy = sinon.spy(IframeBinding, "iframeBinding");

                    spyOn(baseViewPrototype, 'initialize');
                    spyOn(baseViewPrototype, 'beforeRender');
                    spyOn(baseViewPrototype, 'render');
                    spyOn(baseViewPrototype, 'afterRender').andCallThrough();
                });

                afterEach(function () {
                    iframeBinding_spy.restore();
                });

                it('calls before and after render functions when render of baseview is called', function () {
                    var baseView = new BaseView();
                    baseView.render();

                    expect(baseViewPrototype.initialize).toHaveBeenCalled();
                    expect(baseViewPrototype.beforeRender).toHaveBeenCalled();
                    expect(baseViewPrototype.render).toHaveBeenCalled();
                    expect(baseViewPrototype.afterRender).toHaveBeenCalled();
                });

                it('calls iframeBinding function when afterRender of baseview is called', function () {
                    var baseView = new BaseView();
                    baseView.render();
                    expect(baseViewPrototype.afterRender).toHaveBeenCalled();
                    expect(iframeBinding_spy.called).toEqual(true);

                    //check calls count of iframeBinding function
                    expect(iframeBinding_spy.callCount).toBe(1);
                    IframeBinding.iframeBinding();
                    expect(iframeBinding_spy.callCount).toBe(2);
                });
            });


            describe("XBlock rendering", function() {
                var mockXBlockHtml, respondWithMockXBlockFragment, postXBlock;

                mockXBlockHtml = '\n' +
                    '<header class="xblock-header">\n' +
                    '  <div class="header-details">\n' +
                    '    <span>Mock XBlock</span>\n' +
                    '  </div>\n ' +
                    '  <div class="header-actions">\n' +
                    '    <ul class="actions-list">\n' +
                    '      <li class="sr action-item">No Actions</li>\n' +
                    '    </ul>\n' +
                    '  </div>\n' +
                    '</header>\n' +
                    '<article class="xblock-render">\n' +
                    '  <div class="xblock xblock-student_view xmodule_display xmodule_VerticalModule"' +
                    '   data-runtime-class="PreviewRuntime" data-init="XBlockToXModuleShim" data-runtime-version="1"' +
                    '   data-type="None">\n' +
                    '    <p>Mock XBlock</p>\n' +
                    '  </div>\n' +
                    '</article>';

                respondWithMockXBlockFragment = function(requests, mockResponse) {
                    var requestIndex = requests.length - 1;
                    create_sinon.respondWithJson(requests, mockResponse, requestIndex);
                };

                postXBlock = function(requests, resources) {
                    $.ajax({
                        url: "test_url",
                        type: 'GET',
                        success: function(fragment) {
                            baseView.renderXBlockFragment(fragment, this.$el);
                        }
                    });
                    respondWithMockXBlockFragment(requests, {
                        html: mockXBlockHtml,
                        resources: resources
                    });
                    expect(baseView.$el.select('.xblock-header')).toBeTruthy();
                }


                beforeEach(function () {
                    baseView = new BaseView();
                });

                it('can render an xblock with no CSS or JavaScript', function() {
                    var requests = create_sinon.requests(this);
                    $.ajax({
                        url: "test_url",
                        type: 'GET',
                        success: function(fragment) {
                            baseView.renderXBlockFragment(fragment, this.$el);
                        }
                    });
                    respondWithMockXBlockFragment(requests, {
                        html: mockXBlockHtml,
                        resources: []
                    });
                    expect(baseView.$el.select('.xblock-header')).toBeTruthy();
                });

                it('can render an xblock with required CSS', function() {
                    var requests = create_sinon.requests(this),
                        mockCssText = "// Just a comment",
                        mockCssUrl = "mock.css",
                        headHtml;
                    $.ajax({
                        url: "test_url",
                        type: 'GET',
                        success: function(fragment) {
                            baseView.renderXBlockFragment(fragment, this.$el);
                        }
                    });
                    respondWithMockXBlockFragment(requests, {
                        html: mockXBlockHtml,
                        resources: [
                            [
                                "1",
                                {
                                    mimetype: "text/css",
                                    kind: "text",
                                    data: mockCssText
                                }
                            ],
                            [
                                "2",
                                {
                                    mimetype: "text/css",
                                    kind: "url",
                                    data: mockCssUrl
                                }
                            ]
                        ]
                    });
                    expect(baseView.$el.select('.xblock-header')).toBeTruthy();
                    headHtml = $('head').html();
                    expect(headHtml).toContain(mockCssText);
                    expect(headHtml).toContain(mockCssUrl);
                });


                it('can render an xblock with required JavaScript', function() {
                    var requests = create_sinon.requests(this);
                    $.ajax({
                        url: "test_url",
                        type: 'GET',
                        success: function(fragment) {
                            baseView.renderXBlockFragment(fragment, this.$el);
                        }
                    });
                    respondWithMockXBlockFragment(requests, {
                        html: mockXBlockHtml,
                        resources: [
                            [
                                "3",
                                {
                                    mimetype: "application/javascript",
                                    kind: "text",
                                    data: "window.test = 100;"
                                }
                            ]
                        ]
                    });
                    expect(baseView.$el.select('.xblock-header')).toBeTruthy();
                    expect(window.test).toBe(100);
                });
            });
        });
    });
