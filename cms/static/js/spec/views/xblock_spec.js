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
        });
    });
