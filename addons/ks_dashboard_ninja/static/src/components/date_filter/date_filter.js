/**@odoo-module **/

import { Component, useState, useRef } from "@odoo/owl"
import { DateTimeInput } from "@web/core/datetime/datetime_input";
//import { setObjectInCookie, getObjectFromCookie, eraseCookie } from "@ks_dashboard_ninja/js/cookies";
import { parseDateTime, parseDate, formatDate, formatDateTime } from "@web/core/l10n/dates";
import { localization } from "@web/core/l10n/localization";
import { _t } from "@web/core/l10n/translation";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { setObjectInSession, getObjectFromSession, eraseSessionItem } from "@ks_dashboard_ninja/js/cookies";
import { isMobileOS } from "@web/core/browser/feature_detection";

const { DateTime } = luxon;


export class KsDateFilter extends Component{
    setup(){
        this.ks_dashboard_data = this.props.dashboard_data
        this.notification = this.env.services.notification
        this.isMobile = isMobileOS();
        this.ks_date_filter_selections = {
            'l_none': _t('All Time'),
            'l_day': _t('Today'),
            't_week': _t('This Week'),
            'td_week': _t('Week To Date'),
            't_month': _t('This Month'),
            'td_month': _t('Month to Date'),
            't_quarter': _t('This Quarter'),
            'td_quarter': _t('Quarter to Date'),
            't_year': _t('This Year'),
            'td_year': _t('Year to Date'),
            'n_day': _t('Next Day'),
            'n_week': _t('Next Week'),
            'n_month': _t('Next Month'),
            'n_quarter': _t('Next Quarter'),
            'n_year': _t('Next Year'),
            'ls_day': _t('Last Day'),
            'ls_week': _t('Last Week'),
            'ls_month': _t('Last Month'),
            'ls_quarter': _t('Last Quarter'),
            'ls_year': _t('Last Year'),
            'l_week': _t('Last 7 days'),
            'l_month': _t('Last 30 days'),
            'l_quarter': _t('Last 90 days'),
            'l_year': _t('Last 365 days'),
            'ls_past_until_now': _t('Past Till Now'),
            'ls_pastwithout_now': _t('Past Excluding Today'),
            'n_future_starting_now': _t('Future Starting Now'),
            'n_futurestarting_tomorrow': _t('Future Starting Tomorrow'),
            'l_custom': _t('Custom Filter'),
        };
        this.ksDateFilterSelection = false
        this.ksDateFilterStartDateObj = this.ks_dashboard_data.ks_dashboard_start_date ? parseDateTime(this.ks_dashboard_data.ks_dashboard_start_date) : DateTime.now();
        this.ksDateFilterEndDateObj = this.get_initial_date(this.ks_dashboard_data.ks_dashboard_end_date)

        this.rootRef = useRef("rootRef")

        this.items = Object.keys(this.ks_dashboard_data.ks_dashboard_items_ids)
        this.state = useState({
            ks_current_filter : this.ksDateFilterSelection,
            is_show_date_fields : false
        })
        this.state.ks_current_filter = this.ks_dashboard_data.ks_date_filter_selection

        this.custom_date_filter_buttons = [ { name: "Apply", callback: this.onApplyClick.bind(this), classes: 'dash-default-btn bg-white me-2', shouldVisible: true },
                                            { name: "Clear", callback: this._onKsClearDateValues.bind(this), classes: 'dash-btn-red', shouldVisible: true } ]
    }

    get_initial_date(date){
        if(date)    return parseDateTime(date);
        return this.ks_dashboard_data.ks_default_end_time ? DateTime.now().endOf('day') : DateTime.now();
    }

    _ksOnDateFilterMenuSelect(selected_filter_id) {
        this.env.services.ui.block();

        eraseSessionItem('FilterDateData' + this.ks_dashboard_data.ks_dashboard_id);
        this.state.ks_current_filter = selected_filter_id
        if (this.state.ks_current_filter !== 'l_custom'){
            this._onKsApplyDateFilter(this.state.ks_current_filter, false, false)
        }
        else{
            this.ksDateFilterStartDateObj = this.ks_dashboard_data.ks_dashboard_start_date ? parseDateTime(this.ks_dashboard_data.ks_dashboard_start_date) : DateTime.now()
            this.ksDateFilterEndDateObj = this.get_initial_date(this.ks_dashboard_data.ks_dashboard_end_date)
            this.state.is_show_date_fields = true
        }
        this.props.update_mode(this.state.ks_current_filter !== 'l_custom' ? "manager" : "custom_date")
        this.env.services.ui.unblock();

    }

    _onKsApplyDateFilter(selected_filter_id, start_date, end_date) {
        let self = this;
        if(!['l_none', 'l_custom'].includes(selected_filter_id))
            setObjectInSession('FilterDateData' + this.ks_dashboard_data.ks_dashboard_id,
                {'filter_selection': this.state.ks_current_filter, date_range: { start_date, end_date }}, 1);
        self.ksDateFilterSelection = this.state.ks_current_filter;
         if (this.state.ks_current_filter !== "l_custom") {
            this.env.ks_update_date_filter_state(selected_filter_id, false, false);
            this.props.update_mode(this.ks_dashboard_data.ks_dashboard_manager ? "manager" : "user");
        } else {
            if (start_date && end_date) {
                if ( start_date <= end_date ) {
                    start_date = start_date.toString()
                    end_date = end_date.toString()
                    if (start_date === "Invalid date" || end_date === "Invalid date"){
                        this.notification.add(_t("Invalid Date"), { type: "warning"});
                    }else{
                        setObjectInSession('FilterDateData' + this.ks_dashboard_data.ks_dashboard_id,
                            {'filter_selection': this.state.ks_current_filter, date_range: { start_date, end_date }}, 1);
                        this.state.is_show_date_fields = false
                        this.env.ks_update_date_filter_state(selected_filter_id, start_date, end_date)
                        this.props.update_mode(this.ks_dashboard_data.ks_dashboard_manager ? "manager" : "user");
                   }
                } else {
                    this.notification.add(_t("Start date should be less than end date."), { type: "warning"});
                }
            } else {
                let notification_text = !start_date && !end_date ? "Please enter start date and end date." : `Please enter ${ !start_date ? "start" : "end" } date`;
                this.notification.add(_t(notification_text), { type: "warning"});
            }
        }
    }

    change_start_date(args){
        this.ksDateFilterStartDateObj = args
    }

    change_end_date(args){
        this.ksDateFilterEndDateObj = args
    }

    onApplyClick(){
        this._onKsApplyDateFilter('l_custom', this.ksDateFilterStartDateObj, this.ksDateFilterEndDateObj)
    }

    _onKsClearDateValues() {
        eraseSessionItem('FilterDateData' + this.ks_dashboard_data.ks_dashboard_id);
        this.state.ks_current_filter = 'l_none'
        this.state.is_show_date_fields = false
        this.env.ks_update_date_filter_state('l_none', false, false)
        this.props.update_mode(this.ks_dashboard_data.ks_dashboard_manager ? "manager" : "user");
    }

    showDateFilterFields(){
        this.state.is_show_date_fields = true
        this.props.update_mode('custom_date');
    }

} ;
KsDateFilter.props = {
    dashboard_data : { type : Object, optional : true },
    update_mode : { type : Function, optional : true }
}
KsDateFilter.components = { Dropdown, DateTimeInput, DropdownItem }
KsDateFilter.template = "ks_dashboard_ninja.Ks_date_filter"