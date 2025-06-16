/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { eraseSessionItems } from '@ks_dashboard_ninja/js/ks_global_functions';


patch(FormController.prototype,{
    async onRecordSaved(record, changes){
        if(this.model?.config?.resModel === 'ks_dashboard_ninja.board' && this.model.config.resId){
            let field_names = ['ks_dashboard_custom_filters_ids', 'ks_dashboard_defined_filters_ids', 'ks_date_filter_selection',
                                'ks_default_end_time', 'ks_dashboard_start_date', 'ks_dashboard_end_date']
            let is_dn_cookie_related_field_changes = field_names.some(field_name => changes.hasOwnProperty(field_name));
            if(is_dn_cookie_related_field_changes)
                eraseSessionItems(this.model.config.resId,
                    ['PFilter', 'PFilterDataObj', 'Filter', 'CFilter', 'FilterDateData', 'ChartFilter', 'FFilter']);
// TODO : Apply such functionlity that we donot have to give name of the name of the filter as string to erase cookies Also dont need to remove all cookies"

        }
        super.onRecordSaved(record, changes);
    }
});




