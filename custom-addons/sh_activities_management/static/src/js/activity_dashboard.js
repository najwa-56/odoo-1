/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { View } from "@web/views/view";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
const { Component } = owl;
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { _t } from "@web/core/l10n/translation";
import { markup } from "@odoo/owl";


export class ActivityDashboard extends Component {           
    async setup() {        
        super.setup();       
        this.action = useService("action"); 
        this.orm = useService("orm");                               
        this.test = await this.orm.call("activity.dashboard", "get_user_list", [], {});    
        console.log(".....this.test....", this.test);   
        var user_list =this.test;        
        console.log(".....user_list....",user_list);   
        document.getElementById("sh_crm_db_user_id").replaceChildren();
        document.getElementById("sh_crm_db_supervisor_id").replaceChildren();
        console.log(".....this.test....", document.getElementById('all_activity'));
        if(user_list) {
            user_list.users.forEach(function(user) {
                var msg =`<a class="dropdown-item o_ace_filter" data-type="xml" data-value="${user.name}" data-id="${(user.id)}" href="#">${user.name}</a>`;               
                document.getElementById("sh_crm_db_user_id").innerHTML +=markup(msg);                     
            }); 
            user_list.supervisors.forEach(function(user) {
                var msg =`<a class="dropdown-item o_ace_filter" data-type="xml" data-value="${user.name}" data-id="${(user.id)}" href="#">${user.name}</a>`;               
                document.getElementById("sh_crm_db_supervisor_id").innerHTML +=markup(msg);  
            });
        }       
        $('#sh_crm_db_supervisor_ids > option').remove();
        $('#sh_crm_db_user_ids > option').remove();
        // session.user_has_group('sh_activities_management.group_activity_supervisor')
        //     .then(function (has_group) {
        //         if (has_group) {
        //             $('#user_id').removeClass("o_hidden");
        //         }
        //     });
        // session.user_has_group('sh_activities_management.group_activity_manager')
        //     .then(function (has_group) {
        //         if (has_group) {
        //             $('#supervisor_id').removeClass("o_hidden");
        //             $('#user_id').removeClass("o_hidden");
        //         }
        //     });
        var user_list =this.user_list;
        if(user_list) {
            $("#sh_crm_db_supervisor_ids").append('<option data-id="' + user_list.id + '" value="' + user_list.name + '">');
            $("#sh_crm_db_user_ids").append('<option data-id="' + user_list.id + '" value="' + user_list.name + '">');
        }
        // self.render_activity_tbl();
    }
    
    action_all_activities() {               
            var self = this;                           
            // var list_value = JSON.parse("[" + $("#all_activity").val() + "]");
            // var comma_string = list_value.toString();
            // var all_act = comma_string.split(",").map(Number);    
            // this.orm.call("ir.model.data", "xmlid_to_res_model_res_id", ["sh_activities_management_basic.sh_mail_activity_view_form"], {
               
            // });                                 
            // rpc.query({
            //     model: "ir.model.data",
            //     method: "xmlid_to_res_model_res_id",
            //     args: ["sh_activities_management_basic.sh_mail_activity_view_form"],
            // }).then(function (data) {              
            //     self.action.doAction(
            //         {
            //             name: _t("All Activities"),
            //             type: "ir.actions.act_window",
            //             res_model: "mail.activity",
            //             view_mode: "tree,'calendar','pivot','graph',form",
            //             view_type: "form",
            //             views: [
            //                 [false, "list"],
            //                 [false, "calendar"],
            //                 [false, "pivot"],
            //                 [false, "graph"],
            //                 [data, "form"],
            //             ],
            //             domain: ["|", ["active", "=", false], ["active", "=", true]],
            //             target: "current",
            //         },
            //         {}
            //     );
            // });
        }
        
}
ActivityDashboard.template = "activity_dashboard.dashboard";
ActivityDashboard.components = { View,Layout, ControlPanel};
ActivityDashboard.props = { ...standardActionServiceProps };

registry.category("actions").add("activity_dashboard.dashboard", ActivityDashboard,{ force: true });
