/** @odoo-module */

import { registry } from "@web/core/registry";
import { Component, onMounted, onWillStart, useState, useEffect, onWillUpdateProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Many2XAutocomplete } from "@web/views/fields/relational_utils";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";


import { RKTable } from "@sh_activities_management/js/dashboard_components/rk_tbl";


import { ListRenderer } from "@web/views/list/list_renderer";
export class ActivityDashboard extends Component {
    static props = {
        sh_display_cancelled_activities_counter: { type: Boolean, optional: true },
        sh_display_overdue_activities_counter: { type: Boolean, optional: true },
        sh_display_completed_activities_counter: { type: Boolean, optional: true },
        sh_display_planned_activities_counter: { type: Boolean, optional: true },
        sh_display_all_activities_counter: { type: Boolean, optional: true },
    }
    static defaultProps = {
        //cancelText: _t("Back"),
        controlButtons: [],     
    };
    setup() {
        super.setup();
        this.orm = useService("orm");        
        onWillUpdateProps(async (nextProps) => {
            await this.fetchDefaultConfig(nextProps);
        });
        this.state = useState({
            infos: {},
            defaultconfig:{},
            table_stages:[
                {
                    'name': '1',
                    'component':RKTable,
                    'props':{
                        'stage':'New', 
                    }
                },
                {
                    'name': '2',                
                    'component':RKTable,
                    'props':{
                        'stage':'In Progress', 
                    }
                },
                {
                    'name': '3',                
                    'component':RKTable,
                    'props':{
                        'stage':'Done', 
                    }
                },
                {
                    'name': '4',                
                    'component':RKTable,
                    'props':{
                        'stage':'Cancel', 
                    }
                }                                    
            ]
        });

        onWillStart(async () => {
            this.state.infos.activitypelaceholder='Activity Type';
            this.state.infos.userplaceholder='Users';
            this.state.infos.superuserplaceholder='Supervisor';
            this.state.defaultconfig = await this.orm.call("activity.dashboard", 
            "get_default_config", []);
            console.log("....defaultconfig.sh_display_cancelled_activities_counter....",typeof(this.state.defaultconfig));
            this.sh_display_cancelled_activities_counter = this.state.defaultconfig.sh_display_cancelled_activities_counter;
            this.sh_display_overdue_activities_counter=this.state.defaultconfig.sh_display_overdue_activities_counter;
            this.sh_display_completed_activities_counter=this.state.defaultconfig.sh_display_completed_activities_counter;
            this.sh_display_planned_activities_counter=this.state.defaultconfig.sh_display_planned_activities_counter;
            this.sh_display_all_activities_counter=this.state.defaultconfig.sh_display_all_activities_counter;         
        });

        onMounted(async () => {
        
        });

    }
    sh_activity_type_getDomain() {
        return [];
    }
    sh_user_getDomain() {
        return [];
    }
    sh_superuser_getDomain(){
        return [];
    }

    _onchangefilter(){
       
        let x = Math.floor((Math.random() * 100) + 1);
        this.state.table_stages[0].props.stage = x;
        let y = Math.floor((Math.random() * 100) + 1);
        this.state.table_stages[1].props.stage = y;


    }    

    async onUpdateType(value) {      
        if (!value) {
            return;
        }
        else {
            console.log("\n\n==value", value[0].display_name);
            this.state.infos.activitytype = value[0].display_name;            
        }
    }

    async onUpdateUser(value) {
        console.log("\n\n==this.state.infos", this.state)
        if (!value) {
            return;
        }
        else {
            // if (this.state.infos.team){

            // }
            console.log("\n\n=====value", value)
            this.state.infos.user = value[0].display_name;
        }
    }
    async onUpdateSuperUser(value) {
        console.log("\n\n==this.state.infos", this.state)
        if (!value) {
            return;
        }
        else {
            // if (this.state.infos.team){

            // }
            console.log("\n\n=====value", value)
            this.state.infos.superuser = value[0].display_name;
        }
    }
    get HelpdeskSelectCreateDialog() {

    }
   

}
ActivityDashboard.template = "activity_dashboard.dashboard";
ActivityDashboard.components = { RKTable,Many2XAutocomplete,ListRenderer};
ActivityDashboard.props = { 
    ...standardActionServiceProps,
    state: Object,
    sh_display_cancelled_activities_counter:Boolean,
    sh_display_overdue_activities_counter:Boolean, 
    sh_display_completed_activities_counter:Boolean,
    sh_display_planned_activities_counter: Boolean, 
    sh_display_all_activities_counter: Boolean, 
}

registry.category("actions").add("activity_dashboard.dashboard", ActivityDashboard,{ force: true });