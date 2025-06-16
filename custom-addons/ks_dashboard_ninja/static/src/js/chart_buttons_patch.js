/** @odoo-module **/

import { KsItemButton } from '@ks_dashboard_ninja/components/chart_buttons/chart_buttons';
import { CustomDialog } from '@ks_dashboard_ninja/components/charts_insights/charts_insights';
import { patch } from "@web/core/utils/patch";

patch(KsItemButton.prototype,{
     _onButtonClick() {
        let dashboard_data = this.env.getDashboardDataAsObj([])
        let item = dashboard_data.ks_item_data[this.id]
        let openDialog = () => {
            this.env.services.dialog.add(CustomDialog,{
                    ks_dashboard_manager: item.ks_dashboard_manager,
                    ks_dashboard_items: dashboard_data.ks_dashboard_items_ids,
                    ks_dashboard_data: dashboard_data,
                    item: item,
                    ks_dashboard_item_type: item.ks_dashboard_item_type,
                    dashboard_data: dashboard_data,
                    ksdatefilter: 'none',
                    ks_speak: () => {},
                    ksDateFilterSelection: '',
                    pre_defined_filter: {},
                    custom_filter: {},
                    title:"Hello",
                    hideButtons: 0,
                    current_graph: this.__owl__.parent.component,
                    getDomainParams: this.env.ksGetParamsForItemFetch,
                    getDashboardContext: this.env.getContext,
            });
        }

        let self = this
        if(!item.ks_ai_analysis) {
           self.env.services.rpc("/web/dataset/call_kw/ks_dashboard_ninja.arti_int/ks_generate_analysis",{
                 model: 'ks_dashboard_ninja.arti_int',
                 method: 'ks_generate_analysis',
                 args: [[item],[],item.ks_dashboard_id],
                 kwargs:{context: {explain_items_with_ai: true}},
           }).then((result) => {
                if (result){
                    self.env.services.rpc("/web/dataset/call_kw/ks_dashboard_ninja.arti_int/get_ai_explain",{
                        model: 'ks_dashboard_ninja.arti_int',
                        method: 'get_ai_explain',
                        args: [item.id, item.id],
                        kwargs:{ },
                    }).then(function(res) {
                        item.ks_ai_analysis = res
                        openDialog();
                    });
                }
           });
        }
        else {
            openDialog();
        }
    }
});
