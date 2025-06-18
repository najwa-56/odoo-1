/** @odoo-module **/

import { ActionContainer } from "@web/webclient/actions/action_container";
import { patch } from "@web/core/utils/patch";
import { onPatched } from "@odoo/owl";


patch(ActionContainer.prototype,{
    setup(){
        super.setup();
        onPatched( () => {
            if(this.info?.componentProps?.action?.tag === 'ks_dashboard_ninja' || this.info?.componentProps?.action?.tag === 'dashboard_ninja'){
                if(!$('body').hasClass('ks_body_class'))
                    $('body').addClass('ks_body_class');
            }
            else if(this.info?.componentProps?.action?.tag !== 'ks_dashboard_ninja' || this.info?.componentProps?.action?.tag !== 'dashboard_ninja'){
                if($('body').hasClass('ks_body_class'))
                    $('body').removeClass('ks_body_class');
            }
        });
    },

});
