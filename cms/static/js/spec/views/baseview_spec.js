define(["jquery", "underscore", "js/views/baseview", "js/utils/handle_iframe_binding", "sinon"],
    function ($, _, BaseView, IframeBinding, sinon) {

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
        });
    });
