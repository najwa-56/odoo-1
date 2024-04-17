/** @odoo-module */

import { Component, onWillStart, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { useService, useBus } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";
export class ActivityCardsDashboardView extends Component {
    static props = {       
        data_dict_act: { type: Object, optional: true },
    };
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        onWillStart(async () => await this.fetchHierarchy());
        this.state = useState({ data_dict_act: {} });
        useBus(this.env.bus, 'cards_dashboard', (ev) => this._fetchLunchInfos(ev.detail));
        useBus(this.env.bus, 're_render_activity_cards_with_filter', (ev) => this._reRenderCardsWithFilter(ev.detail));

    }

    async fetchHierarchy() {
        this.state.data_dict_act = {}
        const args = [false, false, false, false, false, false,false,false]
        const ActivityCardsData = await this.orm.call("activity.dashboard", "get_activity_count_tbl", args);
        this.state.data_dict_act = ActivityCardsData
    }
    async _reRenderCardsWithFilter(CurrentData) {

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
        
        const cards_args = [filter_date, filter_user, start_date, end_date, filter_supervisor,filter_model,filter_record,filter_type]
        const ActivityCardsData = await this.orm.call("activity.dashboard", "get_activity_count_tbl", cards_args);
        this.state.data_dict_act = ActivityCardsData;

    }

    get getTempActValue() { 
        return this.state.data_dict_act; 
    }

    _onClickCards(ev) {
        let resIdsString = $(ev.target).closest('a').attr('res_ids');
        let resIdsArray = resIdsString.split(',');

        let resIdsNumbers = resIdsArray.map(Number);
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: _t('Activities'),
            res_model: 'mail.activity',
            views: [[false, 'list'], [false, 'kanban'], [false, 'form']],
            domain: [['id', 'in', resIdsNumbers],['active','in',[true,false]]],
        });
    }
    

}
ActivityCardsDashboardView.template = "activity_dashboard_cards.dashboard";