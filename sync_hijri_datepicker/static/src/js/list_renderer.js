odoo.define('sync_hijri_datepicker.ListRenderer', function (require) {
    "use strict";

    var core = require('web.core');
    var ListRenderer = require('web.ListRenderer');
    var field_utils = require('web.field_utils');
    var time = require('web.time');
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

    var FIELD_CLASSES = {
        float: 'o_list_number',
        integer: 'o_list_number',
        monetary: 'o_list_number',
        text: 'o_list_text',
    };
    String.prototype.fromDigits = function () {
        var id = ['۰', '۱', '۲', '۳', '٤', '۵', '٦', '۷', '۸', '۹'];
        return this.replace(/[0-9]/g, function (w) {
            return id[+w]
        });
    }

    ListRenderer.include({
        _convertGregorianToHijri: function (date) {
            var date_split, year, month, day, jd, formatted_date;
            var calendar = $.calendars.instance('gregorian');
            var calendar1 = $.calendars.instance('islamic');
            if (date) {
                if (date.indexOf('-') !== -1) {
                    date_split = date.split('-');
                    year = parseInt(date_split[0]);
                    month = parseInt(date_split[1]);
                    day = parseInt(date_split[2]);
                    jd = calendar.toJD(year, month, day);
                    formatted_date = calendar1.fromJD(jd);
                }
                if (date.indexOf('/') !== -1) {
                    date_split = date.split('/');
                    year = parseInt(date_split[2]);
                    month = parseInt(date_split[0]);
                    day = parseInt(date_split[1]);
                    jd = calendar.toJD(year, month, day);
                    formatted_date = calendar1.fromJD(jd);
                }
                month = calendar1.formatDate('MM', formatted_date);
                var date = calendar1.formatDate('d, yyyy', formatted_date);
                if (this.state.context.lang === 'ar_SY') {
                    date = date.fromDigits();
                    month = _.find(hijriMonths, function (value, key) {
                        if (key === month) {
                            return value;
                        }
                    });
                }
                if (this.state.context.lang === 'ar') {
                    date = date.fromDigits();
                    month = _.find(hijriMonths, function (value, key) {
                        if (key === month) {
                            return value;
                        }
                    });
                }
                if (this.state.context.lang === 'ar_001') {
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
        _renderBodyCell: function (record, node, colIndex, options) {
            var tdClassName = 'o_data_cell';
            if (node.tag === 'button') {
                tdClassName += ' o_list_button';
            } else if (node.tag === 'field') {
                tdClassName += ' o_field_cell';
                var typeClass = FIELD_CLASSES[this.state.fields[node.attrs.name].type];
                if (typeClass) {
                    tdClassName += (' ' + typeClass);
                }
                if (node.attrs.widget) {
                    tdClassName += (' o_' + node.attrs.widget + '_cell');
                }
            }
            if (node.attrs.editOnly) {
                tdClassName += ' oe_edit_only';
            }
            if (node.attrs.readOnly) {
                tdClassName += ' oe_read_only';
            }
            var $td = $('<td>', { class: tdClassName, tabindex: -1 });

            // We register modifiers on the <td> element so that it gets the correct
            // modifiers classes (for styling)
            var modifiers = this._registerModifiers(node, record, $td, _.pick(options, 'mode'));
            // If the invisible modifiers is true, the <td> element is left empty.
            // Indeed, if the modifiers was to change the whole cell would be
            // rerendered anyway.
            if (modifiers.invisible && !(options && options.renderInvisible)) {
                return $td;
            }

            if (node.tag === 'button') {
                return $td.append(this._renderButton(record, node));
            } else if (node.tag === 'widget') {
                return $td.append(this._renderWidget(record, node));
            }
            if (node.attrs.widget || (options && options.renderWidgets)) {
                var $el = this._renderFieldWidget(node, record, _.pick(options, 'mode'));
                return $td.append($el);
            }
            this._handleAttributes($td, node);
            var name = node.attrs.name;
            var field = this.state.fields[name];
            var value = record.data[name];
            var formatter = field_utils.format[field.type];
            var formatOptions = {
                escape: true,
                data: record.data,
                isPassword: 'password' in node.attrs,
            };
            var formattedValue = formatter(value, field, formatOptions);
            if (_.contains(['date', 'datetime'], field.type)) {
                if (formattedValue) {
                    var formattedHijriValue = this._parseDate(value)
                    formattedValue = this._formateDate(formattedValue, formattedHijriValue);
                }
            }
            var title = '';
            if (field.type !== 'boolean') {
                title = formatter(value, field, _.extend(formatOptions, {escape: false}));
            }
            return $td.html(formattedValue).attr('title', title);
        },
        _parseDate: function (v) {
            return v.clone().locale('en').format('YYYY-MM-DD');
        },
        _formateDate: function (formattedValue, formattedHijriValue) {
            var self = this;
            if (formattedHijriValue) {
                return _.map([formattedValue], function (formattedValue) {
                    return formattedValue + ' - ' + _.str.sprintf(_t(self._convertGregorianToHijri(formattedHijriValue)));
                });
            }
        },
        _onWindowClicked: function (event) {
            if ($(event.target).hasClass('calendars-highlight')) {
                return;
            }
            this._super.apply(this, arguments);
        }
    });
});