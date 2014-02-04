define(["domReady", "jquery", "underscore", "gettext", "js/views/baseview",
    "xblock/runtime.v1", "xblock/cms.runtime.v1", "xmodule", "coffee/src/main"],
    function (domReady, $, _, gettext, BaseView, XBlock) {

        var XBlockView = BaseView.extend({
            // takes XBlockInfo as a model

            events: {
              "click .expand-collapse": "toggleExpandCollapse"
            },

            initialize: function() {
                BaseView.prototype.initialize.call(this);
                this.render();
            },

            render: function() {
                return $.ajax({
                    url: this.model.url(),
                    type: 'GET',
                    headers: {
                        Accept: 'application/container-x-fragment+json'
                    },
                    success: _.bind(this.renderXBlock, this)
                });
            },

            renderXBlock: function(data) {
                var value, _fn, _i, _len, _ref;
                this.$el.html(data.html);
                _ref = data.resources;
                _fn = function(value) {
                    var hash, resource;
                    hash = value[0];
                    if (window.loadedXBlockResources == null) {
                        window.loadedXBlockResources = [];
                    }
                    if (__indexOf.call(window.loadedXBlockResources, hash) < 0) {
                        resource = value[1];
                        switch (resource.mimetype) {
                            case "text/css":
                                switch (resource.kind) {
                                    case "text":
                                        $('head').append("<style type='text/css'>" + resource.data + "</style>");
                                        break;
                                    case "url":
                                        $('head').append("<link rel='stylesheet' href='" + resource.data + "' type='text/css'>");
                                }
                                break;
                            case "application/javascript":
                                switch (resource.kind) {
                                    case "text":
                                        $('head').append("<script>" + resource.data + "</script>");
                                        break;
                                    case "url":
                                        $.getScript(resource.data);
                                }
                                break;
                            case "text/html":
                                switch (resource.placement) {
                                    case "head":
                                        $('head').append(resource.data);
                                }
                        }
                        return window.loadedXBlockResources.push(hash);
                    }
                };
                for (_i = 0, _len = _ref.length; _i < _len; _i++) {
                    value = _ref[_i];
                    _fn(value);
                }
                XBlock.initializeBlock(this.$el.find('.xblock-student_view'));
                return this.delegateEvents();
            }
        });

        return XBlockView;
    }); // end define();
