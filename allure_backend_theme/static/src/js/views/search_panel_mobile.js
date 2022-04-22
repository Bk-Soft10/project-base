odoo.define('allure_backend_theme.SearchPanelMobile', function (require) {

const config = require('web.config');
if (!config.device.isMobile) {
    return;
}

const core = require('web.core');
var SearchPanel = require('web.SearchPanel');

const qWeb = core.qweb;

SearchPanel.include({

    tagName: 'details',

    events: _.extend({}, SearchPanel.prototype.events, {
        'click .btn_search_panel_result': function(e) {
            e.preventDefault();
            this.el.removeAttribute('open');
        },
    }),

    _getCategorySelection: function () {
        var self = this;
        return _.reduce(_.keys(this.categories), function(selection, categoryId) {
            var category = self.categories[categoryId];
            if (category.activeValueId) {
                selection.push({
                    values: _.map([category.activeValueId].concat(
                            self._getAncestorValueIds(category, category.activeValueId)
                        ), function (valueId) {
                            return category.values[valueId].display_name;
                        }),
                    icon: category.icon,
                    color: category.color,
                });
            }
            return selection;
        }, []);
    },

    _getFilterSelection: function () {
        var self = this;

        var getCheckedValues = function(values) {
            return _.map(_.filter(_.keys(values), function(valueId) {
                return values[valueId].checked;
            }), function(valueId) { return values[valueId].name; });
        };

        return _.reduce(_.keys(this.filters), function (selection, filterId) {
            var filter = self.filters[filterId];
            var values = [];
            if (filter.groups) {
                values = _.flatten(_.map(_.keys(filter.groups), function(groupId) {
                    return getCheckedValues(filter.groups[groupId].values);
                }));
            } else if (filter.values) {
                values = getCheckedValues(filter.values);
            }
            if (!_.isEmpty(values)) {
                selection.push({
                    values: values,
                    icon: filter.icon,
                    color: filter.color,
                });
            }
            return selection;
        }, []);
    },

    _render: function () {
        this._super.apply(this, arguments);
        this.$el.prepend(qWeb.render('SearchPanel.MobileView', {
            categories: this._getCategorySelection(),
            filters: this._getFilterSelection(),
        }));
    },

});

});
