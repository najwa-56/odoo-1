/** @odoo-module */
/** A magical journey into the world of ticket dashboards.*/

import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { ActivityTableDashboardView } from "@sh_activities_management/js/dashboard_components/table_component";
import { ActivityCardsDashboardView } from "@sh_activities_management/js/dashboard_components/cards_component";
import { Many2XAutocomplete } from "@web/views/fields/relational_utils";
import { DateTimeInput } from "@web/core/datetime/datetime_input";
import { _t } from "@web/core/l10n/translation";
import { ListRenderer } from "@web/views/list/list_renderer";




// Let the dashboard extravaganza begin!
export class ActivityDashboard extends Component {

    // Initializing state and setting the stage for some serious ticket magic.
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.user = useService("user");
        this.company=useService("company")
        this.currentCompanyId = useService("company").currentCompany.id;
        this.state = useState({
            infos: {},
            model: { id: false },
            selected_model: false,
            user: { id: false },
            selected_user: false,
            superuser: { id: false },
            selected_superuser:false,   
            activitytype: { id: false },
            selected_type:false,            
            activeActions: {},        
            table_data_actvity: []
        });

       
        // Preparing for the ride by fetching essential data.
        onWillStart(async () => {
            
            const getModel = await this.orm.call("activity.dashboard", "get_model", []);
            this.getModel = getModel;   
            
            const getUser = await this.orm.call("activity.dashboard", "get_user", []);
            this.getUser = getUser; 
            this.getsuperUser = getUser;   
            // const getActivityData = await this.orm.call("activity.dashboard", "get_activity_tbl", []);
            // this.state.table_data_actvity = getActivityData;
            const getType = await this.orm.call("activity.dashboard", "get_type", []);           
            this.gettype = getType;
            this.is_activity_manager = await this.user.hasGroup("sh_activities_management.group_activity_manager");
            this.is_activity_supervisor = await this.user.hasGroup("sh_activities_management.group_activity_supervisor");
            this.is_activity_user = await this.user.hasGroup("sh_activities_management.group_activity_user");
            this.is_system_user = await this.user.hasGroup("base.group_system");

            const args = [this.currentCompanyId];
            const get_is_model_activate = await this.orm.call("activity.dashboard", "get_model_activate", args);
            this.is_activate_model = get_is_model_activate[0];
            this.document_models = get_is_model_activate[1];
        });
       
    }
     // Updating the start date - because even activities have a beginning.
     async UpdateStartDates(date = false) {
        if (date) {
            const start_date = new Date(date.c.year, date.c.month - 1, date.c.day);
            this.state.start_date = start_date;
            this._triggerBusToUpdateState();
        } else {
            this.state.start_date = false;
            this._triggerBusToUpdateState();
        }
    }

    // Updating the end date - because even activities need closure.
    async UpdateEndDates(date = false) {
        if (date) {
            const end_date = new Date(date.c.year, date.c.month - 1, date.c.day);
            this.state.end_date = end_date;
            this._triggerBusToUpdateState();
        } else {
            this.state.end_date = false;
            this._triggerBusToUpdateState();
        }
    }

    // Handling filter changes - where even filters have a dramatic impact.
    _onchangefilter(ev) {
        // The filter dance - when options change, the magic begins!
        var date_options_value = false;
        if (ev.target.value != 'all' && ev.target.value != 'custom') {
            date_options_value = ev.target.value;
            this.state.date_options_value = date_options_value;
            this.state.select_date_type = date_options_value;
            this._triggerBusToUpdateState();
        }

        // When all is selected, the world (of tickets) is your oyster!
        if (ev.target.value == 'all') {
            var date_options_value = false;
            this.state.date_options_value = date_options_value;
            this.state.select_date_type = date_options_value;
            this._triggerBusToUpdateState();
        }

        // Custom mode - because sometimes tickets need a bespoke experience.
        if (ev.target.value == 'custom') {
            this.state.select_date_type = false;
            this.state.date_options_value = 'custom';
            this._triggerBusToUpdateState();
        }
    }
    // Updating Activity Type
    get many2XAutocompletePropsActivityType(){
        return {
            resModel: "mail.activity.type",
            value: this.state.selected_type ? this.state.selected_type : '',
            fieldString: _t("Select a Activity Type"),
            getDomain: this.getDomaintype.bind(this),
            activeActions: {},
            update: this.updatetype.bind(this),
            placeholder: _t("Select a Activity Type .."),
            quickCreate: null,
        };
    }   
    getDomaintype() {
        return [];
    }   
    updatetype(selectedMenus) {
        if (selectedMenus) {
            const userWithId = this.gettype.find(activitytype => activitytype.id === selectedMenus[0].id);
            this.state.activitytype = selectedMenus[0];
            this.state.selected_type = userWithId.name;
            this._triggerBusToUpdateState();
        } else {
            this.state.activitytype = { id: false };
            this.state.selected_type = false;
            this._triggerBusToUpdateState();
        }
    }

    // Updating Supervisor
     
    get many2XAutocompletePropsSuperUser(){
        return {
            resModel: "res.users",
            value: this.state.selected_superuser ? this.state.selected_superuser : '',
            fieldString: _t("Select a Supervisor"),
            getDomain: this.getDomainsuperuser.bind(this),
            activeActions: {},
            update: this.updatesuperuser.bind(this),
            placeholder: _t("Select a Supervisor..."),
            quickCreate: null,
        };
    }

    getDomainsuperuser() {
        return [];
    }   
    updatesuperuser(selectedMenus) {
        if (selectedMenus) {
            const userWithId = this.getsuperUser.find(superuser => superuser.id === selectedMenus[0].id);
            this.state.superuser = selectedMenus[0];
            this.state.selected_superuser = userWithId.name;
            this._triggerBusToUpdateState();
        } else {
            this.state.superuser = { id: false };
            this.state.selected_superuser = false;
            this._triggerBusToUpdateState();
        }
    }


    // Updateting User
    get many2XAutocompletePropsUser(){
        return {
            resModel: "res.users",
            value: this.state.selected_user ? this.state.selected_user : '',
            fieldString: _t("Select a User"),
            getDomain: this.getDomainuser.bind(this),
            activeActions: {},
            update: this.updateuser.bind(this),
            placeholder: _t("Select a User..."),
            quickCreate: null,
        };
    }

    getDomainuser() {
        return [];
    }   
    updateuser(selectedMenus) {
        if (selectedMenus) {
            const userWithId = this.getUser.find(user => user.id === selectedMenus[0].id);
            this.state.user = selectedMenus[0];
            this.state.selected_user = userWithId.name;
            this._triggerBusToUpdateState();
        } else {
            this.state.user = { id: false };
            this.state.selected_user = false;
            this._triggerBusToUpdateState();
        }
    }

    // Updating The Model
    get many2XAutocompletePropsModel(){
        return {
            resModel: "ir.model",
            value: this.state.selected_model ? this.state.selected_model : '',
            fieldString: _t("Select a Model"),
            getDomain: this.getDomainModel.bind(this),
            activeActions: {},
            update: this.updateModel.bind(this),
            placeholder: _t("Select a Model..."),
            quickCreate: null,
        };
    }

    getDomainModel() {
        return [['id','in',this.document_models]];
    }
    // Updating the Team - because teamwork makes the ticket dream work.
    updateModel(selectedMenus) {
        if (selectedMenus) {
            const userWithId = this.getModel.find(model => model.id === selectedMenus[0].id);
            this.state.model = selectedMenus[0];
            this.state.selected_model = userWithId.name;
            this._triggerBusToUpdateState();
        } else {
            this.state.team = { id: false };
            this.state.selected_model = false;
            this._triggerBusToUpdateState();
        }
    }

    // Updating the Team - because teamwork makes the ticket dream work.
    updateModel(selectedMenus) {
        if (selectedMenus) {
            const userWithId = this.getModel.find(model => model.id === selectedMenus[0].id);
            this.state.model = selectedMenus[0];
            this.state.selected_model = userWithId.name;
            this._triggerBusToUpdateState();
        } else {
            this.state.team = { id: false };
            this.state.selected_model = false;
            this._triggerBusToUpdateState();
        }
    }

    // Triggering the ticket bus - "Please update state, we've got tickets to show!"
    _triggerBusToUpdateState() {
        this.env.bus.trigger('re_render_activity_cards_with_filter', { CurrentData: this.state });
        this.env.bus.trigger('re_render_activity_Tables_with_filter', { CurrentData: this.state });
    }
}

// The grand template for the Ticket Dashboard - where tickets come alive!
ActivityDashboard.template = "activity_main_dashboard.dashboard";

// Components that make this Ticket Dashboard a star-studded event.
ActivityDashboard.components = {
    ActivityTableDashboardView,
    ActivityCardsDashboardView,
    Many2XAutocomplete,
    ListRenderer,
    DateTimeInput
};

// Props that ensure this dashboard is action-packed!
ActivityDashboard.props = {
    ...standardActionServiceProps
};

registry.category("actions").add("action_activity_dashboard", ActivityDashboard, { force: true });