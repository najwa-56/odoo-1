/** @odoo-module */

import { Component, onWillStart, useState } from "@odoo/owl";
import { useService, useBus } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { Pager } from "@web/core/pager/pager";
import { _t } from "@web/core/l10n/translation";
const DEFAULT_LIMIT = 8;
export class ActivityTableDashboardView extends Component {

    // static props = {       
    //     data_dict_act: { type: Object, optional: true },
    // };
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        onWillStart(async () => await this.fetchHierarchy());
        this.state = useState({ data_dict_act: this.props.data_dict_act,
        
        // pagerProps: {
        //     offset: 0,
        //     limit: DEFAULT_LIMIT,
        //     total: this.props.data_dict_act.count_acts,
        // }, 
        });
        console.log("\n\n\nthis.props.data_dict_act",this)
        this.orm = useService("orm");
        useBus(this.env.bus, 'tables_dashboard', (ev) => this._fetchLunchInfos(ev.detail));
        useBus(this.env.bus, 're_render_activity_Tables_with_filter', (ev) => this._reRenderTablesWithFilter(ev.detail));

    }
    async fetchHierarchy() {
        this.state.data_dict_act = {}
        const args = [false, false, false, false, false, false,false,false]
        const ActivityTablesData = await this.orm.call("activity.dashboard", "get_activity_tbl", args);
        this.state.data_dict_act = ActivityTablesData
    }
    async _reRenderTablesWithFilter(CurrentData) {

        const normalCurrentData = Object.assign({}, CurrentData.CurrentData);
        const filter_model = normalCurrentData.model.id ?? false;
        const filter_record = false;
        const filter_type = normalCurrentData.activitytype.id ?? false;
        const filter_user = normalCurrentData.user.id ?? false;
        const filter_supervisor = normalCurrentData.superuser.id ?? false;
        const filter_date = normalCurrentData.date_options_value ?? false;               
        var start_date = normalCurrentData.start_date ?? false;
        
        if (start_date) {
            start_date = start_date.toLocaleDateString('en-US', { year: 'numeric', month: '2-digit', day: '2-digit' });
        }
        
        var end_date = normalCurrentData.end_date ?? false;
        if (end_date) {
            end_date = end_date.toLocaleDateString('en-US', { year: 'numeric', month: '2-digit', day: '2-digit' });
        }
        // var limit = this.state.pagerProps.limit
        // var offset = this.state.pagerProps.offset
        const tables_args = [filter_date, filter_user, start_date, end_date, filter_supervisor,filter_model,filter_record,filter_type]//,limit,offset]
        const ActivityTablesData = await this.orm.call("activity.dashboard", "get_activity_tbl", tables_args);
        this.state.data_dict_act = ActivityTablesData;
        // this.state.pagerProps.total = ActivityTablesData[0].count_acts
    }

    get getTempActValue() { 
        return this.state.data_dict_act; 
    }
    // /**
    //  * @param {Object} param0
    //  * @param {number} param0.offset
    //  * @param {number} param0.limit
    //  */
    // onUpdatePager({ offset, limit }) {
    //     this.state.pagerProps.offset = offset;
    //     this.state.pagerProps.limit = limit;
    //     this._reRenderTablesWithFilter(this.state.CurrentData);
    // }

    async _onClickCancel(ev) {
        let ActivityID = $(ev.target).parents('tr').find("#activity_id").attr("value")
        const result = await this.orm.call("mail.activity", "action_cancel_dashboard", [ActivityID]);
        console.log("result",result)
        if (result.cancelled == true) {
            location.reload(true);
        }
    }
    async _onClickUnarchive(ev) {
        let ActivityID = $(ev.target).parents('tr').find("#activity_id").attr("value")
        const result = await this.orm.call("mail.activity", "unarchive_dashboard", [ActivityID]);
        console.log("result",result)
        if (result.unarchive == true) {
            location.reload(true);
        }
    }
    async _onClickDone(ev) {
        let ActivityID = $(ev.target).parents('tr').find("#activity_id").attr("value")
        $('#popup_activity_id').val(ActivityID);
        $('.modal').modal('show');
    }
    async _onClickDonePopup(ev) {
        const result = await this.orm.call("mail.activity", "action_done_dashboard", [$('#popup_activity_id').val(),$('#activity_feedback').val()]);
        console.log("result",result)
        if (result.completed == true) {
            location.reload(true);
        }
    }
}
ActivityTableDashboardView.template = "activity_dashboard_table.dashboard";
ActivityTableDashboardView.components = { Pager };
ActivityTableDashboardView.props = {
    ...standardActionServiceProps,
};