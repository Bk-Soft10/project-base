/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { KeepLast } from "@web/core/utils/concurrency";
import { debounce } from "@web/core/utils/timing";
import { renderToElement } from "@web/core/utils/render";


publicWidget.registry.faqSearch = publicWidget.Widget.extend({
    selector: '#search_query',
    xmlDependencies: ['/website_faqs/static/src/xml/search_result.xml'],

    events: {
        'input .dev-query': '_onInput',
        'focusout': '_onFocusOut',
        'keydown .dev-query': '_onKeydown',
    },
    autocompleteMinWidth: 1,

    init: function () {
        this._super.apply(this, arguments);
        this.keepLast = new KeepLast();
        this._onFocusOut = debounce(this._onFocusOut, 100);
        this.rpc = this.bindService("rpc");
    },

    start: function () {
        this.limit = 3;
        return this._super.apply(this, arguments);

    },

    _fetch: function () {
        return this.rpc('/faq/autocomplete',
            {
                'term': $('.dev-query').val(),
                'max_nb_chars': Math.round(Math.max(this.autocompleteMinWidth, parseInt(this.$el.width())) * 0.22),
            }
        );
    },

    _render: function (res) {
        var self = this;
        var $prevMenu = this.$menu;
        this.$el.toggleClass('dropdown show', !!res);
        if (res) {
            var faqs = res['faqs'];
            this.$menu = $(renderToElement('website_faqs.faqSearchBar.autocomplete', {
                faqs: faqs,

            }));
            this.$menu.css('min-width', this.autocompleteMinWidth);
            this.$el.append(this.$menu);
        }
        if ($prevMenu) {
            $prevMenu.remove();
        }
    },

    _onInput: function () {
        var self = this;
        if ($('.dev-query').val().length < this.limit) {
            return;
        }
        this.keepLast.add(this._fetch())
            .then(function (result) {
                self._render(result);
            });
    },

    _onFocusOut: function () {
        if (!this.$el.has(document.activeElement).length) {
            this._render();
        }
    },

    _onKeydown: function (ev) {
        switch (ev.which) {
            case $.ui.keyCode.ESCAPE:
                this._render();
                break;
        }
    },
})


$(document).ready(function () {
    $(".feedback").click(function () {
        $("#take_feedback").replaceWith("<span class='text-muted'>Thank you for your feedback</span>")
    });
});