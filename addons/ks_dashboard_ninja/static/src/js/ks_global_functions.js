/** @odoo-module **/

import { getCurrency } from "@web/core/currency";
import { formatFloat, formatInteger } from "@web/views/fields/formatters";
import { localization } from "@web/core/l10n/localization";
import { eraseSessionItem } from "@ks_dashboard_ninja/js/cookies";

export const globalfunction = {
    ksNumIndianFormatter(num, digits){

            var negative;
            var si = [{
                value: 1,
                symbol: ""
            },
            {
                value: 1E3,
                symbol: "Th"
            },
            {
                value: 1E5,
                symbol: "Lakh"
            },
            {
                value: 1E7,
                symbol: "Cr"
            },
            {
                value: 1E9,
                symbol: "Arab"
            }
            ];
            if (num < 0) {
                num = Math.abs(num)
                negative = true
            }
            var rx = /\.0+$|(\.[0-9]*[1-9])0+$/;
            var i;
            for (i = si.length - 1; i > 0; i--) {
                if (num >= si[i].value) {
                    break;
                }
            }
            if (negative) {
                return "-" + (num / si[i].value).toFixed(digits).replace(rx, "$1") + si[i].symbol;
            } else {
                return (num / si[i].value).toFixed(digits).replace(rx, "$1") + si[i].symbol;
            }

        },
    ksNumFormatter(num, digits) {
            var negative;
            var si = [{
                    value: 1,
                    symbol: ""
                },
                {
                    value: 1E3,
                    symbol: "k"
                },
                {
                    value: 1E6,
                    symbol: "M"
                },
                {
                    value: 1E9,
                    symbol: "G"
                },
                {
                    value: 1E12,
                    symbol: "T"
                },
                {
                    value: 1E15,
                    symbol: "P"
                },
                {
                    value: 1E18,
                    symbol: "E"
                }
            ];
            if (num < 0) {
                num = Math.abs(num)
                negative = true
            }
            var rx = /\.0+$|(\.[0-9]*[1-9])0+$/;
            var i;
            for (i = si.length - 1; i > 0; i--) {
                if (num >= si[i].value) {
                    break;
                }
            }
            if (negative) {
                return "-" + (num / si[i].value).toFixed(digits).replace(rx, "$1") + si[i].symbol;
            } else {
                return (num / si[i].value).toFixed(digits).replace(rx, "$1") + si[i].symbol;
            }
        },
    ks_monetary(value, currency_id) {
           ///get currency changed ////
            var currency = getCurrency(currency_id);
            if (!currency) {
                return value;
            }
            if (currency.position === "after") {
                return value += ' ' + currency.symbol;
            } else {
                return currency.symbol + ' ' + value;
            }
        },
    _onKsGlobalFormatter(ks_record_count, ks_data_format, ks_precision_digits){
            var self = this;
            if (ks_data_format == 'exact'){
                return formatFloat(ks_record_count, {digits: [0, ks_precision_digits]})
//                return field_utils.format.float(ks_record_count, Float64Array,{digits:[0,ks_precision_digits]});
            }else{
                if (ks_data_format == 'indian'){
                    return self.ksNumIndianFormatter( ks_record_count, 1);
                }else if (ks_data_format == 'colombian'){
                    return self.ksNumColombianFormatter( ks_record_count, 1, ks_precision_digits);
                }else{
                    return self.ksNumFormatter(ks_record_count, 1);
                }
            }
        },
     ksNumColombianFormatter(num, digits, ks_precision_digits) {
            var negative;
            var si = [{
                    value: 1,
                    symbol: ""
                },
                {
                    value: 1E3,
                    symbol: ""
                },
                {
                    value: 1E6,
                    symbol: "M"
                },
                {
                    value: 1E9,
                    symbol: "M"
                },
                {
                    value: 1E12,
                    symbol: "M"
                },
                {
                    value: 1E15,
                    symbol: "M"
                },
                {
                    value: 1E18,
                    symbol: "M"
                }
            ];
            if (num < 0) {
                num = Math.abs(num)
                negative = true
            }
            var rx = /\.0+$|(\.[0-9]*[1-9])0+$/;
            var i;
            for (i = si.length-1; i > 0; i--) {
                if (num >= si[i].value) {
                    break;
                }
            }

            if (si[i].symbol === 'M'){
//                si[i].value = 1000000;
                num = parseInt(num) / 1000000
                // changes
                num = formatInteger(num)
                if (negative) {
                    return "-" + num + si[i].symbol;
                } else {
                    return num + si[i].symbol;
                }
                }else{
                    if (num % 1===0){
                    // changes
                    num = formatInteger(num)
                    }else{
//                        num = field_utils.format.float(num, Float64Array, {digits:[0,ks_precision_digits]});
                        num = formatFloat(num, {digits: [0, ks_precision_digits]})
                    }
                    if (negative) {
                        return "-" + num;
                    } else {
                        return num;
                    }
                }

        }

}


function onAudioEnded (ev){
    ev.currentTarget?.parentElement?.querySelector('.voice-cricle')?.classList.toggle("d-none");
    ev.currentTarget?.parentElement?.querySelector('.comp-gif')?.classList.toggle("d-none");
}

function ks_get_current_gridstack_config(gridstackRootElement){
            if (gridstackRootElement && gridstackRootElement.gridstack){
                var items = gridstackRootElement.gridstack.el.gridstack.engine.nodes;
            }
            let grid_config = {}
            if (items){
                for (var i = 0; i < items.length; i++) {
                    grid_config[items[i].id] = {
                        'x': items[i].x, 'y': items[i].y,
                        'w': items[i].w, 'h': items[i].h,
                    }
                }
            }
            return grid_config;
        }

function convert_data_to_utc(list_view_data) { // TODO Can be moved to python side for faster computation
    list_view_data = JSON.parse(list_view_data);
    let datetime_format = localization.dateTimeFormat;
    let date_format = localization.dateFormat;
    if (list_view_data && list_view_data.type === "ungrouped") {
        if (list_view_data.date_index) {
            let index_data = list_view_data.date_index;
            for (let i = 0; i < index_data.length; i++) {
                for (let j = 0; j < list_view_data.data_rows.length; j++) {
                    var index = index_data[i]
                    var date = list_view_data.data_rows[j]["data"][index]
                    if (date) {
                        if (list_view_data.fields_type[index] === 'date'){
                            list_view_data.data_rows[j]["data"][index] = luxon.DateTime.fromJSDate(new Date(date + " UTC")).toFormat?.(date_format);
                        }else if(list_view_data.fields_type[index] === 'datetime'){
                            list_view_data.data_rows[j]["data"][index] = luxon.DateTime.fromJSDate(new Date(date + " UTC")).toFormat?.(datetime_format);
                        }
                    }
                }
            }
        }
    }
    return list_view_data;
}


function eraseSessionItems(dashboard_id, obj_name_list_to_be_deleted = []){
    obj_name_list_to_be_deleted.forEach( (name) => {
        eraseSessionItem(name + dashboard_id)
    });
}

return {
    globalfunction: globalfunction,
    onAudioEnded,
    ks_get_current_gridstack_config,
    convert_data_to_utc,
    eraseSessionItems
}
