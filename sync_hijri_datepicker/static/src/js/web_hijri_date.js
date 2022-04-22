odoo.define('sync_hijri_datepicker.datepicker', function (require) {
    "use strict";

    var core = require('web.core');
    var datepicker = require('web.datepicker');
    var time = require('web.time');
    var FieldDate = require('web.basic_fields').FieldDate;

    var _t = core._t;

    var hijriMonths = {
        "Muharram": "‎مُحَرَّم",
        "Safar": "‎صَفَر",
        "Rabi' al-awwal": "‎رَبِيْعُ الأَوّل",
        "Rabi' al-thani": "‎رَبِيْعُ الثَّانِي",
        "Jumada al-awwal": "‎جَمَادِي الأَوّل",
        "Jumada al-thani": "‎جَمَادِي الثَّانِي",
        "Rajab": "‎رَجَب",
        "Sha'aban": "‎شَعْبَان",
        "Ramadan": "‎رَمَضَان",
        "Shawwal": "‎شَوَّال",
        "Dhu al-Qi'dah": "‎ذُوالْقَعْدَة",
        "Dhu al-Hijjah": "‎ذُوالْحِجَّة"
    }

    String.prototype.fromDigits = function () {
        var id = ['۰', '۱', '۲', '۳', '٤', '۵', '٦', '۷', '۸', '۹'];
        return this.replace(/[0-9]/g, function (w) {
            return id[+w]
        });
    }

    datepicker.DateWidget.include({
        start: function () {
            var self = this;
            this.$input = this.$('input.o_datepicker_input');
            this.$input_hijri = this.$('input.o_hijri');
            this.$input_hijri.click(function (e) {
                e.preventDefault();
                self.$input_hijri.calendarsPicker('show');
            });
            this.$input_hijri.calendarsPicker({
                calendar: $.calendars.instance('islamic', this.options.locale),
                dateFormat: 'M d, yyyy',
                closeOnDateSelect: false,
                onSelect: this._convertDateToHijri.bind(this),
            });
            this.__libInput++;
            this.$el.datetimepicker(this.options);
            this.__libInput--;
            this._setReadonly(false);
        },
        _convertGregorianToHijri: function (date) {
            var year, month, day, jd, formatted_date;
            var calendar = $.calendars.instance('islamic');
            if (date && !_.isUndefined(date)) {
                date = moment(date).locale('en');
                month = parseInt(date.format('M'));
                day = parseInt(date.format('D'));
                year = parseInt(date.format('YYYY'));
                jd = $.calendars.instance('gregorian').toJD(year, month, day);
                formatted_date = calendar.fromJD(jd);
                var month = calendar.formatDate('MM', formatted_date);
                var date = calendar.formatDate('d, yyyy', formatted_date);
                if (this.options.locale == 'ar') {
                    date = date.fromDigits();
                    month = _.find(hijriMonths, function (value, key) {
                        if (key === month) {
                            return value;
                        }
                    });
                }
                return _.str.sprintf("%s %s", month, date);
            }
        },
        _convertDateToHijri: function (date) {
            if (!date || date.length === 0) {
                return false;
            }
            $(document).on('click', '.calendars a', function (e) {
                e.preventDefault();
                e.stopImmediatePropagation();
                return false;
            });
            var jd = $.calendars.instance('islamic').toJD(parseInt(date[0].year()), parseInt(date[0].month()), parseInt(date[0].day()));
            var formatted_date = $.calendars.instance('gregorian').fromJD(jd);
            var date_value = moment(time.str_to_date(formatted_date)).add(1, 'days');
            this.setValue(this._parseClient(date_value));
            this.trigger("datetime_changed");

        },
        _parseDate: function (v) {
            return v.clone().locale('en').format('YYYY-MM-DD');
        },
        setValue: function (value) {
            this._super.apply(this, arguments);
            var parsed_date = value ? this._parseDate(value) : null;
            var hijri_value = parsed_date ? this._convertGregorianToHijri(parsed_date) : null;
            this.$input_hijri.val(hijri_value);
        },
        destroy: function () {
            if (this.$el) {
                this.__libInput++;
                this.$el.datetimepicker('destroy');
                this.__libInput--;
            }
        },
        _onInputClicked: function (e) {
            if (e && e.target && ! $(e.target).hasClass('o_hijri')){
                return this._super();
            }
        },
    });
    FieldDate.include({
        _renderReadonly: function () {
            var self = this;
            this._super.apply(this, arguments);
            if (this.value) {
                this.datewidget = this._makeDatePicker();
                var $div = $('<div/>');
                var value = this.value ? this.datewidget._formatClient(this.value) : '';
                var parsed_date = this.value ? this.datewidget._parseDate(this.value) : '';
                var hijri_value = parsed_date ? this.datewidget._convertGregorianToHijri(parsed_date) : '';
                $('<div>', {
                    class: this.$el.attr('class'),
                    text: value,
                }).appendTo($div);
                $('<div>', {
                    class: this.$el.attr('class'),
                    text: hijri_value,
                }).appendTo($div);
                this.datewidget.appendTo('<div>').then(function () {
                    self._replaceElement($div);
                });
            }
        },
    })
});
