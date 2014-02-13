define(["domReady", "jquery", "underscore", "gettext", "js/views/baseview"],
    function (domReady, $, _, gettext, BaseView) {

        var XBlockView = BaseView.extend({
            // takes XBlockInfo as a model

            events: {
                "click .expand-collapse": "toggleExpandCollapse"
            },

            initialize: function() {
                BaseView.prototype.initialize.call(this);
            },

            render: function() {
                var self = this;
                return $.ajax({
                    url: this.model.url(),
                    type: 'GET',
                    headers: {
                        Accept: 'application/container-x-fragment+json'
                    },
                    success: function(fragment) {
                        self.renderXBlockFragment(fragment, this.$el);
                    }
                });
            }
        });

        return XBlockView;
    }); // end define();
