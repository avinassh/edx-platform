define([ "jquery", "js/spec/create_sinon", "URI", "js/views/xblock", "js/models/xblock_info"],
    function ($, create_sinon, URI, XBlockView, XBlockInfo) {

        describe("XBlockView", function() {
            var model, xblockView, mockXBlockHtml, mockResponse, respondWithMockXBlockFragment;

            beforeEach(function () {
                model = new XBlockInfo({
                    id: 'testCourse/branch/published/block/verticalFFF',
                    display_name: 'Test Unit',
                    category: 'vertical'
                });
                xblockView = new XBlockView({
                    model: model
                });
            });

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
            mockResponse = {
                html: mockXBlockHtml,
                "resources": []
            };

            respondWithMockXBlockFragment = function(requests) {
                var requestIndex = requests.length - 1;
                create_sinon.respondWithJson(requests, mockResponse, requestIndex);
            };

            it('can render a nested xblock', function() {
                var requests = create_sinon.requests(this);
                xblockView.render();
                respondWithMockXBlockFragment(requests);

                expect(xblockView.$el.select('.xblock-header')).toBeTruthy();
            });

            describe("XBlock rendering", function() {
                var postXBlockRequest;

                postXBlockRequest = function(requests, resources) {
                    $.ajax({
                        url: "test_url",
                        type: 'GET',
                        success: function(fragment) {
                            xblockView.renderXBlockFragment(fragment, this.$el);
                        }
                    });
                    respondWithMockXBlockFragment(requests, {
                        html: mockXBlockHtml,
                        resources: resources
                    });
                    expect(xblockView.$el.select('.xblock-header')).toBeTruthy();
                };

                it('can render an xblock with no CSS or JavaScript', function() {
                    var requests = create_sinon.requests(this);
                    postXBlockRequest(requests, []);
                    expect(xblockView.$el.select('.xblock-header')).toBeTruthy();
                });

                it('can render an xblock with required CSS', function() {
                    var requests = create_sinon.requests(this),
                        mockCssText = "// Just a comment",
                        mockCssUrl = "mock.css",
                        headHtml;
                    postXBlockRequest(requests, [
                        ["hash1", { mimetype: "text/css", kind: "text", data: mockCssText }],
                        ["hash2", { mimetype: "text/css", kind: "url", data: mockCssUrl }]
                    ]);
                    expect(xblockView.$el.select('.xblock-header')).toBeTruthy();
                    headHtml = $('head').html();
                    expect(headHtml).toContain(mockCssText);
                    expect(headHtml).toContain(mockCssUrl);
                });

                it('can render an xblock with required JavaScript', function() {
                    var requests = create_sinon.requests(this);
                    postXBlockRequest(requests, [
                        ["hash3", { mimetype: "application/javascript", kind: "text", data: "window.test = 100;" }]
                    ]);
                    expect(xblockView.$el.select('.xblock-header')).toBeTruthy();
                    expect(window.test).toBe(100);
                });

                it('can render an xblock with required HTML', function() {
                    var requests = create_sinon.requests(this),
                        mockHeadTag = "<title>Test Title</title>";
                    postXBlockRequest(requests, [
                        ["hash4", { mimetype: "text/html", placement: "head", data: mockHeadTag }]
                    ]);
                    expect(xblockView.$el.select('.xblock-header')).toBeTruthy();
                    expect($('head').html()).toContain(mockHeadTag);
                });
            });
        });
    });
