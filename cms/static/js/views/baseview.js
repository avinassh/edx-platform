define(["jquery", "underscore", "backbone", "js/utils/handle_iframe_binding", "xblock/runtime.v1"],
    function ($, _, Backbone, IframeUtils, XBlock) {
        /*  This view is extended from backbone with custom functions 'beforeRender' and 'afterRender'. It allows other
         views, which extend from it to access these custom functions. 'afterRender' function of BaseView calls a utility
         function 'iframeBinding' which modifies iframe src urls on a page so that they are rendered as part of the DOM.
         Other common functions which need to be run before/after can also be added here.
         */

        var BaseView = Backbone.View.extend({
            events: {
                "click .ui-toggle-expansion": "toggleExpandCollapse"
            },

            //override the constructor function
            constructor: function(options) {
                _.bindAll(this, 'beforeRender', 'render', 'afterRender');
                var _this = this;
                this.render = _.wrap(this.render, function (render) {
                    _this.beforeRender();
                    render();
                    _this.afterRender();
                    return _this;
                });

                //call Backbone's own constructor
                Backbone.View.prototype.constructor.apply(this, arguments);
            },

            beforeRender: function() {
            },

            render: function() {
                return this;
            },

            afterRender: function() {
                IframeUtils.iframeBinding(this);
            },

            toggleExpandCollapse: function(event) {
                var target = $(event.target);
                event.preventDefault();
                target.toggleClass('expand').toggleClass('collapse');
                target.closest('.is-collapsible, .window').toggleClass('collapsed');
            },

            /**
             * Renders an xblock fragment into the specifed element. The fragment has two attributes:
             *   html: the HTML to be rendered
             *   resources: any JavaScript or CSS resources that the HTML depends upon
             * @param fragment The fragment returned from the xblock_handler
             * @param element The element into which to render the fragment (defaults to this.$el)
             */
            renderXBlockFragment: function(fragment, element) {
                var value, applyResource, i, len, resources, resource, xblockElement;
                if (!element) {
                    element = this.$el;
                }

                applyResource = function(value) {
                    var hash, resource, head;
                    hash = value[0];
                    if (!window.loadedXBlockResources) {
                        window.loadedXBlockResources = [];
                    }
                    if (_.indexOf(window.loadedXBlockResources, hash) < 0) {
                        resource = value[1];
                        head = $('head');
                        if (resource.mimetype === "text/css") {
                            if (resource.kind === "text") {
                                head.append("<style type='text/css'>" + resource.data + "</style>");
                            } else if (resource.kind === "url") {
                                head.append("<link rel='stylesheet' href='" + resource.data + "' type='text/css'>");
                            }
                        } else if (resource.mimetype === "application/javascript") {
                            if (resource.kind === "text") {
                                head.append("<script>" + resource.data + "</script>");
                            } else if (resource.kind === "url") {
                                $.getScript(resource.data);
                            }
                        } else if (resource.mimetype === "text/html") {
                            if (resource.kind === "head") {
                                head.append(resource.data);
                            }
                        }
                        window.loadedXBlockResources.push(hash);
                    }
                };

                element.html(fragment.html);
                resources = fragment.resources;
                for (i = 0, len = resources.length; i < len; i++) {
                    resource = resources[i];
                    applyResource(resource);
                }
                xblockElement = element.find('.xblock-student_view');
                if (xblockElement.length > 0) {
                    XBlock.initializeBlock(xblockElement);
                }
                return this.delegateEvents();
            }
        });

        return BaseView;
    });
