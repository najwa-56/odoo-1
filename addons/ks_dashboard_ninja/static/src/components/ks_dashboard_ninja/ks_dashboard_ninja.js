/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { Component, onRendered, onWillStart, useState, onPatched, useChildSubEnv, useSubEnv,
            onMounted, onWillRender, useRef, useEffect, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { jsonrpc } from "@web/core/network/rpc_service";
import { useService, useBus } from "@web/core/utils/hooks";
import { localization } from "@web/core/l10n/localization";
import { session } from "@web/session";
import { download } from "@web/core/network/download";
import { useChildRef } from "@web/core/utils/hooks";
import { BlockUI } from "@web/core/ui/block_ui";
import { WebClient } from "@web/webclient/webclient";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { patch } from "@web/core/utils/patch";
import { isMobileOS } from "@web/core/browser/feature_detection";
import { loadBundle } from '@web/core/assets';
import { FormViewDialog} from '@web/views/view_dialogs/form_view_dialog';
import { renderToElement } from "@web/core/utils/render";
import { convert_data_to_utc, eraseSessionItems } from '@ks_dashboard_ninja/js/ks_global_functions'
import { KschatwithAI } from '@ks_dashboard_ninja/components/chatwithAI/ks_chat';
import { DateTimePicker } from "@web/core/datetime/datetime_picker";
import { DateTimeInput } from "@web/core/datetime/datetime_input";
const { DateTime } = luxon;
import {formatDate,formatDateTime} from "@web/core/l10n/dates";
import {parseDateTime,parseDate,} from "@web/core/l10n/dates";
import { KsHeader } from '@ks_dashboard_ninja/components/Header/Header'
import { KsItems } from "@ks_dashboard_ninja/components/ks_items/ks_items";
import { setObjectInSession, getObjectFromSession, eraseSessionItem } from "@ks_dashboard_ninja/js/cookies";
import { debounce } from "@bus/workers/websocket_worker_utils";


export class KsDashboardNinja extends Component {
    static props = ["*"];

    setup() {
        let self = this;
        this.actionService = useService("action");
        this.uiService = useService("ui");
        this.dialogService = useService("dialog");
        this.notification = useService("notification");
        this._rpc = useService("rpc");
        this.dialogService = useService("dialog");
        this.user = useService("user");
        this.headerRootRef =  useChildRef();
        this.gridStackRootRef =  useChildRef();
        this.header = this.headerRootRef
        this.footer =  useRef("ks_dashboard_footer");
        this.main_body = useRef("ks_main_body");
        this.reload_menu_option = {
            reload:this.props.action.context.ks_reload_menu,
            menu_id: this.props.action.context.ks_menu_id
        };
        this.ks_mode = 'active';
        this.action_manager = parent;
        this.name = "ks_dashboard";
        this.ksIsDashboardManager = false;
        this.dashboard_domain_data = {}
        this.recent_searches = useState({ value : []})
        this.file_type_magic_word = {
            '/': 'jpg',
            'R': 'gif',
            'i': 'png',
            'P': 'svg+xml',
        };
        this.ksAllowItemClick = true;

        //Dn Filters Iitialization

        this.date_format = localization.dateFormat
        this.datetime_format = localization.dateTimeFormat
        this.ks_date_filter_data;


        // To make sure date filter show date in specific order.
        this.ks_date_filter_selection_order = ['l_day', 't_week', 't_month', 't_quarter','t_year',
            'td_week','td_month','td_quarter', 'td_year','n_day','n_week', 'n_month', 'n_quarter', 'n_year',
            'ls_day','ls_week', 'ls_month', 'ls_quarter', 'ls_year', 'l_week', 'l_month', 'l_quarter', 'l_year',
            'ls_past_until_now', 'ls_pastwithout_now','n_future_starting_now', 'n_futurestarting_tomorrow',
            'l_custom'
        ];

        this.ks_dashboard_id = this.props.action.params.ks_dashboard_id;
        this.isReloadOnFirstCreate = this.props.action?.params?.isReloadOnFirstCreate ? true : false
        this.explain_ai_whole = true;
        this.explain_ai_whole = this.props.action.params.explain_ai_whole === undefined ? true : false;

         var ks_fav_filter_remove = $('.ks_dn_fav_filters').find('.ks_fav_filters_checked');
         if (ks_fav_filter_remove.length){
             var ks_fav_filter = ks_fav_filter_remove.attr('fav-name');
             ks_fav_filter_remove.removeClass('ks_fav_filters_checked');
             this.ks_remove_favourite_filter(ks_fav_filter);
         }

        this.gridstackConfig = {};
        this.grid = true;
        this.state = useState({
            ks_dashboard_name: '',
            ks_multi_layout: false,
            ks_dash_name: '',
            ks_dashboard_manager :false,
            date_selection_data: {},
            date_selection_order :[],
            ks_show_create_layout_option : true,
            ks_show_layout :false,
            ks_selected_board_id:false,
            ks_child_boards:false,
            ks_dashboard_data:{},
            ks_dn_pre_defined_filters:[],
            ks_dashboard_items:[],
            update:false,
            ksDateFilterSelection :'none',
            pre_defined_filter :{},
            ksDateFilterStartDate: DateTime.now(),
            ksDateFilterEndDate:DateTime.now(),
            stateToggle: false,
            dialog_header: true,
            should_loading: true,
            itemsToUpdateList: []

        })
        this.ksChartColorOptions = ['default', 'cool', 'warm', 'neon'];
        this.ksDateFilterSelection = false;
        this.ksDateFilterStartDate = false;
        this.ksDateFilterEndDate = false;
        this.ksUpdateDashboard = {};
        $("head").append('<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">');
        if(this.props.action.context.ks_reload_menu){
            this.trigger_up('reload_menu_data', { keep_open: true, scroll_to_bottom: true});
        }
        var context = {
            ksDateFilterSelection: this.ksDateFilterSelection,
            ksDateFilterStartDate: this.ksDateFilterStartDate,
            ksDateFilterEndDate: this.ksDateFilterEndDate,
        }
        this.dn_state = {}
        this.dn_state['user_context']=context
        this.isFavFilter = false;
        this.activeFavFilterName = "FavouriteFilter"
        this.ks_speeches = [];
        onWillStart(this.willStart);
        onWillRender(this.dashboard_mount);

        this.modelsListForAutoUpdate = []
        this.env.services.bus_service.addChannel('ks_notification')

        useEffect(() => {
            this.ks_fetch_items_data();
        }, ()=>[]
        )

        useEffect( () => {
            if(this.ks_dashboard_data.ks_set_interval){
                this._debounced_items_for_update = debounce(this.update_dashboard_items.bind(this), parseInt(this.ks_dashboard_data.ks_set_interval))
                this.env.services.bus_service.subscribe('Update: Dashboard Items', (detail) => {
                                                                            this.modelsListForAutoUpdate.push(detail.model)
                                                                            this._debounced_items_for_update();});
                return this.env.services.bus_service.removeEventListener('Update: Dashboard Items', (detail) => {
                                                                            this.modelsListForAutoUpdate.push(detail.model)
                                                                            this._debounced_items_for_update();})
            }
        }, ()=>[])

        onMounted(() => {

             $(".modal-footer").find("button").addClass('d-none')
             let filterFacetCountTag = this.header.el.querySelector('.filters-amount')
        });

        onRendered(()=>{
            if(this.isReloadOnFirstCreate){
                this.isReloadOnFirstCreate = false;
                if(this.props.action.params && this.props.action.params.isReloadOnFirstCreate)
                    this.props.action.params.isReloadOnFirstCreate = false
                this.env.services.menu.reload();
                this.notification.add(_t('New Dashboard is successfully created'),{
                    title:_t("New Dashboard"),
                    type: 'success',
                });
            }
        })
        // TODO: make items independent , graph component,etc  should not be dependent on some other components,
        // TODO: presently we are using many functions in env , can be removed to make component fully independent


        useChildSubEnv({
            getContext : this.getContext.bind(this),
            ksGetParamsForItemFetch: (item_id) => this.ksGetParamsForItemFetch(item_id),
           ks_update_date_filter_state: (selected_filter_id, start_date, end_date) => this.ks_update_date_filter_state(selected_filter_id, start_date, end_date),
            update_dashboard_filters: (domainsToUpdate) => this.update_dashboard_filters(domainsToUpdate),
            replace_dashboard_filters: (domain_data) => this.replace_dashboard_filters(domain_data),
            onKsEditLayoutClick: () => this.onKsEditLayoutClick(),
            isMobile: this.isMobile,
            update_dashboard_mode: this.update_dashboard_mode.bind(this),
            get mode(){ return self.ks_mode},
            getDashboardDataAsObj: this.getDashboardDataAsObj.bind(this),
            gridStackRootRef: this.gridStackRootRef,
            isExplainDashboardWithAi: this.isExplainDashboardWithAi,
        })
    }

    get isMobile(){
        return isMobileOS();
    }

    get isExplainDashboardWithAi(){
        return this.props.action.params.explain_ai_whole ? true : false;
    }

    willStart(){
        let self = this;
        let def;
        if (this.reload_menu_option.reload && this.reload_menu_option.menu_id) {
            def = this.getParent().actionService.ksDnReloadMenu(this.reload_menu_option.menu_id);
        }
        this.setFilterObjFromCookies();
        return $.when(def, loadBundle("ks_dashboard_ninja.ks_dashboard_lib")).then(function() {
            return self.ks_fetch_data().then(function(){
            });
        });
    }

    update_dashboard_items(){
        let itemsToUpdateList = []
        this.modelsListForAutoUpdate?.forEach( (model_name) => {
            itemsToUpdateList.push( ...this.ks_dashboard_data.ks_model_item_relation[model_name] || [])
        })
        this.state.itemsToUpdateList = JSON.parse(JSON.stringify(itemsToUpdateList))
        this.modelsListForAutoUpdate = []
    }

    getDashboardDataAsObj(params){ // params - list of parameters to be get in child components , empty list return whole data
        let data = {}
        params.forEach( (param) => {
            if(this.ks_dashboard_data[param]){
                data[param] = this.ks_dashboard_data[param]
            }
        })
        return Object.keys(data).length ? data : this.ks_dashboard_data;
    }

    setFilterObjFromCookies(){
        let dashboard_domain_data_from_cky = getObjectFromSession('Filter' + this.ks_dashboard_id)
        this.dashboard_domain_data = dashboard_domain_data_from_cky ?? {}
    }

    makeCtxFromCookies(){
        let dateFilterCookieObj = getObjectFromSession('FilterDateData' + this.ks_dashboard_id);
        let context = {}
        if (dateFilterCookieObj != null){
            context = {
                ksDateFilterSelection: dateFilterCookieObj.filter_selection ?? false,
                ksDateFilterStartDate: false, ksDateFilterEndDate: false,
            }
            if(context.ksDateFilterSelection === 'l_custom'){
                try {
                    context.ksDateFilterStartDate = dateFilterCookieObj.date_range.start_date
                    context.ksDateFilterEndDate = dateFilterCookieObj.date_range.end_date
                } catch (error) {
                    context.ksDateFilterStartDate = false
                    context.ksDateFilterEndDate = false
                    eraseSessionItem('FilterDateData' + this.ks_dashboard_id);
                }
            }
            let ctx_to_be_added = { ...session.user_context, ...{ allowed_company_ids: this.env.services.company.activeCompanyIds }}
            return Object.assign(context, ctx_to_be_added);

        }
        let ctx_to_be_added = { ...session.user_context, ...{ allowed_company_ids: this.env.services.company.activeCompanyIds }}
        return Object.assign(context, ctx_to_be_added);
    }

    ks_fetch_data(){
        let self = this;
        return jsonrpc("/web/dataset/call_kw",{
            model: 'ks_dashboard_ninja.board',
            method: 'ks_fetch_dashboard_data',
            args: [ self.ks_dashboard_id ],
            kwargs : { context: self.makeCtxFromCookies() },
        }).then(function(result) {
            if(self.props?.action?.params?.dashboard_data){
                self.ks_dashboard_data = JSON.parse(JSON.stringify(self.props.action.params.dashboard_data))
            }
            else{
                self.ks_dashboard_data = result;
            }
            self.ks_dashboard_item_length = self.ks_dashboard_data.ks_dashboard_items_ids.length
            self.ks_dashboard_data.ks_ai_explain_dash = self.props.action.params.explainWithAi ? true : false
            self.ks_dashboard_data['ks_dashboard_id'] = self.props.action.params.ks_dashboard_id
            self.ks_dashboard_data['context'] = self.getContext()
            self.ks_dashboard_data['ks_ai_dashboard'] = false

            self.ks_favourite_filters = JSON.parse(JSON.stringify(self.ks_dashboard_data.ks_dashboard_favourite_filter))
        });
    }

    async ks_fetch_items_data(){
        let self = this;
        let items_promises = []
        let item_ids = self.ks_dashboard_data.ks_dashboard_items_ids
        await Promise.all(
            item_ids.map(async (item_id) => {
                const itemData = await jsonrpc("/web/dataset/call_kw",{
                                                        model: "ks_dashboard_ninja.board",
                                                        method: "ks_fetch_item",
                                                        args : [[item_id], self.ks_dashboard_id, self.ksGetParamsForItemFetch(item_id)],
                                                        kwargs: { context: self.getContext() }
                                                    })
                if(itemData[item_id].ks_list_view_data){
                    itemData[item_id].ks_list_view_data = convert_data_to_utc(itemData[item_id].ks_list_view_data)
                }
                Object.assign(self.ks_dashboard_data.ks_item_data, itemData)

            })
        );
        this.state.should_loading = false

    }

    getContext() {
        let context = {
            ksDateFilterSelection: this.ks_dashboard_data?.ks_date_filter_selection ?? false,
            ksDateFilterStartDate: this.ks_dashboard_data?.ks_date_filter_selection === 'l_custom' ? this.ks_dashboard_data.ks_dashboard_start_date : false,
            ksDateFilterEndDate: this.ks_dashboard_data?.ks_date_filter_selection === 'l_custom' ? this.ks_dashboard_data.ks_dashboard_end_date : false,
        }
        var ctx_to_be_added = { ...session.user_context, ...{ allowed_company_ids: this.env.services.company.activeCompanyIds }}
        return Object.assign(context, ctx_to_be_added);
    }

    update_dashboard_mode(mode){
        this.ks_mode = mode;
    }

    ksGetParamsForItemFetch(item_id) {
        let self = this;

        let model1 = self.ks_dashboard_data.ks_item_model_relation[item_id][0];
        let model2 = self.ks_dashboard_data.ks_item_model_relation[item_id][1];

        var ks_domain_1 = self.dashboard_domain_data[model1] && self.dashboard_domain_data[model1].domain || [];
        var ks_domain_2 = self.dashboard_domain_data[model2] && self.dashboard_domain_data[model2].domain || [];
        return {
            ks_domain_1: ks_domain_1,
            ks_domain_2: ks_domain_2,
        }
    }

    update_dashboard_filters(domainsToUpdate){ // params:- domainsToUpdate ( Should be object with key as model_name )
        let itemsToUpdateList = []
        Object.keys(domainsToUpdate).forEach( (model) => {
            this.dashboard_domain_data[model] ??= {}
            this.dashboard_domain_data[model] = domainsToUpdate[model]
            itemsToUpdateList.push( ...this.ks_dashboard_data.ks_model_item_relation[model] || [])
            if(!Object.keys(this.dashboard_domain_data[model].sub_domains ?? {}).length){
                delete this.dashboard_domain_data[model]
            }
        })
        if(!Object.keys(this.dashboard_domain_data).length){
            eraseSessionItems(this.ks_dashboard_id, ['PFilter', 'PFilterDataObj', 'Filter', 'CFilter'])
        }
        this.state.itemsToUpdateList = JSON.parse(JSON.stringify(itemsToUpdateList))
    }

    replace_dashboard_filters(domain_data){ // params:- domain_data ( Should be object with key as model_name, replace the existing domain obj )
        let itemsToUpdateList = []
        Object.keys(this.dashboard_domain_data).forEach( (model) => {
            itemsToUpdateList.push( ...this.ks_dashboard_data.ks_model_item_relation[model] || [] )
        })
        Object.keys(domain_data).forEach( (model) => {
            itemsToUpdateList.push( ...this.ks_dashboard_data.ks_model_item_relation[model] || [] )
        })
        this.dashboard_domain_data = domain_data
        this.state.itemsToUpdateList = JSON.parse(JSON.stringify(itemsToUpdateList))
        this.state.ksDateFilterSelection = 'none'
    }


    get ks_get_current_dashboard_data(){
        return this.ks_dashboard_data
    }


    dashboard_mount(){
        var self = this;
        var items = Object.values(self.ks_dashboard_data.ks_item_data)
    }


    ksRenderDashboard(){
        let self = this;
        if (self.ks_dashboard_data.ks_child_boards) self.ks_dashboard_data.name = this.ks_dashboard_data.ks_child_boards[self.ks_dashboard_data.ks_selected_board_id][0];
        self.ksRenderDashboardMainContent();
    }

    ksRenderDashboardMainContent(){
        var self = this;
        if (isMobileOS() && $('#ks_dn_layout_button :first-child').length > 0) {
            $('.ks_am_element').append($('#ks_dn_layout_button :first-child')[0].innerText);
            $(self.header.el).find("#ks_dn_layout_button").addClass("ks_hide");
        }
        if (Object.keys(self.ks_dashboard_data.ks_item_data).length) {
        // todo  implement below mentioned function
            self._renderDateFilterDatePicker();
            $(self.header.el).find('.ks_dashboard_link').removeClass("ks_hide");
        } else if (!Object.keys(self.ks_dashboard_data.ks_item_data).length) {
            $(self.header.el).find('.ks_dashboard_link').addClass("ks_hide");
        }
    }

    _renderDateFilterDatePicker() {
        var self = this;
        $(self.header.el).find(".ks_dashboard_link").removeClass("ks_hide");
        self._KsGetDateValues();
    }

    loadDashboardData(date = false){
        var self = this;
        $(self.header.el).find(".custom_date_filter_section").removeClass("ks_hide");
        $(self.header.el).find(".ks_dashboard_top_settings").addClass("d-none");
        $(self.header.el).find("#favFilterMain").addClass("ks_hide");
        $(self.header.el).find(".filters_section").addClass("ks_hide");
    }

    _KsGetDateValues() {
        var self = this;
        var date_filter_selected = self.ks_dashboard_data.ks_date_filter_selection;
        if (self.ksDateFilterSelection == 'l_none'){
                var date_filter_selected = self.ksDateFilterSelection;
        }
        $(self.header.el).find('#' + date_filter_selected).addClass("ks_date_filter_selected global-filter");

        if (self.ks_dashboard_data.ks_date_filter_selection === 'l_custom') {
            var ks_end_date = self.ks_dashboard_data.ks_dashboard_end_date;
            var ks_start_date = self.ks_dashboard_data.ks_dashboard_start_date;
            var start_date = parseDateTime(ks_start_date, self.datetime_format)
            var end_date = parseDateTime(ks_end_date, self.datetime_format)
            self.state.ksDateFilterStartDate = start_date
            self.state.ksDateFilterEndDate = end_date

            $(self.header.el).find('.ks_date_input_fields').removeClass("ks_hide");
            $(self.header.el).find('.ks_date_filter_dropdown').addClass("ks_btn_first_child_radius");
        } else if (self.ks_dashboard_data.ks_date_filter_selection !== 'l_custom') {
            $(self.header.el).find('.ks_date_input_fields').addClass("ks_hide");
        }
    }


    ks_update_date_filter_state(selected_filter_id, ksDateFilterStartDate, ksDateFilterEndDate){
        let self = this;
        self.ks_dashboard_data.ks_date_filter_selection = selected_filter_id;
        self.ks_dashboard_data.ks_dashboard_start_date = ksDateFilterStartDate
        self.ks_dashboard_data.ks_dashboard_end_date = ksDateFilterEndDate
        self.state.itemsToUpdateList = JSON.parse(JSON.stringify(this.ks_dashboard_data.ks_dashboard_items_ids))
    }

    ks_dashboard_item_action(e){
        this.ksAllowItemClick = false;
    }

    stoppropagation(ev){
        ev.stopPropagation();
        this.ksAllowItemClick = false;
    }

    ksOnLayoutSelection(layout_id){
        var self = this;
        var selected_layout_name = this.ks_dashboard_data.ks_child_boards[layout_id][0];
        var selected_layout_grid_config = this.ks_dashboard_data.ks_child_boards[layout_id][1];
        this.gridstackConfig = JSON.parse(selected_layout_grid_config);
        Object.entries(this.gridstackConfig).forEach((x,y)=>{
            self.grid.update($(self.main_body.el).find(".grid-stack-item[gs-id=" + x[0] + "]")[0],{ x:x[1]['x'], y:x[1]['y'], w:x[1]['w'], h:x[1]['h'],autoPosition:false});
        });
    }

    _onKsSaveLayoutClick(){
        var self = this;
        self._ksRenderActiveMode();
    }

    _ksRenderActiveMode(){
        var self = this
        if (self.grid && $('.grid-stack').data('gridstack')) {
            $('.grid-stack').data('gridstack').disable();
        }
    }

    ks_remove_update_interval(){
        var self = this;
        if (self.ksUpdateDashboard) {
            Object.values(self.ksUpdateDashboard).forEach(function(itemInterval) {
                clearInterval(itemInterval);
            });
            self.ksUpdateDashboard = {};
        }
    }

    onKsEditLayoutClick(e) {
        var self = this;
        self.ksAllowItemClick = false;
        self._ksRenderEditMode();
    }

    _ksRenderEditMode(){
        let self = this;
        self.ks_remove_update_interval();
    }

}

KsDashboardNinja.components = { KsHeader, KsItems };
KsDashboardNinja.template = "ks_dashboard_ninja.KsDashboardNinjaHeader"
registry.category("actions").add("ks_dashboard_ninja", KsDashboardNinja);

const ks_dn_webclient ={
    async loadRouterState(...args) {
        var self = this;
        const sup = await super.loadRouterState(...args);
        const ks_reload_menu = async (id) =>  {
            this.menuService.reload().then(() => {
                self.menuService.selectMenu(id);
            });
        }
        this.actionService.ksDnReloadMenu = ks_reload_menu;
        return sup;
    },
};
patch(WebClient.prototype, ks_dn_webclient)