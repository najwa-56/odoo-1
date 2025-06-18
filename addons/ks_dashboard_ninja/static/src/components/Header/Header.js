/**@odoo-module **/

import { Component, useState} from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { useForwardRefToParent } from "@web/core/utils/hooks";
import { download } from "@web/core/network/download";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { KsDateFilter } from '@ks_dashboard_ninja/components/date_filter/date_filter';
import { ks_get_current_gridstack_config } from '@ks_dashboard_ninja/js/ks_global_functions'
import { DNFilter } from '@ks_dashboard_ninja/components/dn_filter/dn_filter';
import { isMobileOS } from "@web/core/browser/feature_detection";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { FormViewDialog} from '@web/views/view_dialogs/form_view_dialog';
import { useService } from "@web/core/utils/hooks";
import { eraseSessionItems } from '@ks_dashboard_ninja/js/ks_global_functions';


export class KsHeader extends Component{
    static props = {
        dashboard_data: {type:Object, optional:true },
        mode : { type: String },
        headerRootRef: { type: Function, optional: true },
    }
    static components = { Dropdown, DropdownItem, KsDateFilter, DNFilter }
    static template = "ks_dashboard_ninja.Ks_dashboard_ninja_header"


    setup(){
        this.ks_dashboard_data = this.props.dashboard_data
        this.action = this.env.services.action
        this.uiService = useService("ui");
        this.action = useService("action");
        this.notification = useService("notification");
        this._rpc = this.env.services.rpc
        this.ks_dashboard_id = this.ks_dashboard_data.ks_dashboard_id
        this.isMobile = isMobileOS();
        this.headerRootRef = useForwardRefToParent("headerRootRef");
        this.items_length = this.ks_dashboard_data.ks_dashboard_items_ids.length
        this.state = useState({
            mode:  this.props.mode ,    // types - [ "manager", "user", "mobile", "layout", "custom_date" ]
            isDashboardBookmarked: this.ks_dashboard_data.is_bookmarked
        });
        this.dialogService = this.env.services.dialog

        this.tempSelectedLayoutId = JSON.parse(JSON.stringify(this.ks_dashboard_data.ks_selected_board_id))
        this.tempDashboardName = JSON.parse(JSON.stringify(this.ks_dashboard_data.name))

        this.dropdowns = [
            {   name: "Edit Layout", modes: ["manager", "custom_date"],
                func: ()=>this.onKsEditLayoutClick(), svg: "ks_dashboard_ninja.header_edit_svg" },
            {   name: "Bookmark Dashboard", modes: ["manager", "user", "custom_date"],
                func: ()=>this.updateBookmark(), svg: "ks_dashboard_ninja.bookmark" },
            {   name: "Capture Dashboard", modes: ["manager", "user", "custom_date"],
                func: ()=> this.dashboardImageUpdate(), svg: "ks_dashboard_ninja.capture" },
            {   name: "Settings", svg: "ks_dashboard_ninja.setting", modes: ["manager", "custom_date"],
                dropdown_items: [  {name: "Dashboard Settings" , svg: "ks_dashboard_ninja.setting-2", func: (ev)=>this.ksOnDashboardSettingClick(ev), class : '', modes: ["manager", "custom_date"],},
                        {name: "Delete the Dashboard", svg: "ks_dashboard_ninja.trash_svg", func: this.ksOnDashboardDeleteClick.bind(this), class : '', modes: ["manager", "custom_date"],},
                        {name: "Create New Dashboard", svg: "ks_dashboard_ninja.add-square", func:()=>this.ksOnDashboardCreateClick(), class : '', modes: ["manager", "custom_date"],},
                        {name: "Generate Dashboard with AI", svg: "ks_dashboard_ninja.illustrator", func:()=>this.kscreateaidashboard(), class : '', modes: ["manager", "custom_date"],},
                        {name: "Duplicate Current Dashboard", svg: "ks_dashboard_ninja.copy", func:(ev)=>this.ksOnDashboardDuplicateClick(ev), class : '', modes: ["manager", "custom_date"],}],    },
            {   name: "More", svg: "ks_dashboard_ninja.more", modes: ["manager", "user", "custom_date"],
                dropdown_items: [  {name: "Import Item" , svg: "ks_dashboard_ninja.download_svg", func: () => this.ksImportItemJson(), class : '', modes: ["manager", "custom_date"],},
                        {name: "Export Dashboard", svg: "ks_dashboard_ninja.document-upload", func:()=>this.ksOnDashboardExportClick(), class : '', modes: ["manager","user", "custom_date"],},
                        {name: "Import Dashboard", svg: "ks_dashboard_ninja.download_svg", func:()=>this.ksOnDashboardImportClick(), class : '', modes: ["manager", "custom_date"],}]   },
        ]

        this.header_mode_buttons = { "edit" : { buttons : [{ name: "Discard", callback: this._onDiscardLayoutChanges.bind(this), classes: 'dash-default-btn bg-white me-2', shouldVisible: true },
                                                            { name: "Save as New Layout", callback: this.onSaveNewLayoutClick.bind(this), classes: 'dash-btn-red me-2 ks-bg-violet', shouldVisible: this.props.dashboard_data.multi_layouts },
                                                            { name: "Save Layout", callback: this._onKsSaveLayoutClick.bind(this), classes: 'dash-btn-red', shouldVisible: true } ] },
                                     "layout": { buttons : [{ name: "Set Default Layout", callback: this._ksSetLayoutAsDefault.bind(this), classes: 'dash-btn-red', shouldVisible: true},
                                                            { name: "Discard", callback: this.discardLayoutSelection.bind(this), classes: 'dash-default-btn bg-white', shouldVisible: true}] } }

    }

    update_mode(mode){
        if(mode !== 'edit'){
           mode = this.ks_dashboard_data.ks_dashboard_manager ? "manager" : "user"
        }
        this.state.mode = mode
    }

    dashboardImageUpdate(){
        let image_element = document.querySelector('.ks_dashboard_main_content');
        if(!document.querySelector('.ks_dashboard_main_content')?.childNodes.length){
            image_element = document.querySelector('.main-box');
        }
        let self = this;
        this.uiService.block();
        let canvas = html2canvas(image_element,  {
                          height: image_element.clientHeight + 186,
                          width: image_element.clientWidth,
                          windowWidth: image_element.scrollWidth,
                          windowHeight: image_element.scrollHeight,
                          scrollY: 0,
                          scrollX: 0,
                          x: image_element.scrollLeft,
                          y: image_element.scrollTop < 600 ? image_element.scrollTop < 50 ? image_element.scrollTop :
                                    image_element.scrollTop - 150 : image_element.scrollTop - 650,
                        }).then((canvas) => {
                                    let image = canvas.toDataURL("image/png");
                                    self._rpc("/web/dataset/call_kw/ks_dashboard_ninja.board/saveImage",{
                                                        model: 'ks_dashboard_ninja.board',
                                                        method: 'save_dashboard_image',
                                                        args: [[self.ks_dashboard_id]],
                                                        kwargs:{image: image},
                                                    }).then((result) => {
                                                            this.uiService.unblock();
                                                    });
        });
        this.notification.add(_t('Dashboard image updated successfully!'),{
                            title:_t("Dashboard Image Refreshed"),
                            type: 'success',
                        });
    }

    restoreController(){
        let self = this;
        let js_id = self.action.currentController.jsId
        self.action.restore(js_id)
    }

    _onDiscardLayoutChanges(){
        this.restoreController();
    }

    async updateBookmark(){
        let updatedBookmarks = await this._rpc("/web/dataset/call_kw/ks_dashboard_ninja.board/update_bookmarks",{
            model: 'ks_dashboard_ninja.board',
            method: 'update_bookmarks',
            args: [[this.ks_dashboard_id]],
            kwargs:{},
        });
        updatedBookmarks = updatedBookmarks[1]
        this.state.isDashboardBookmarked = !this.state.isDashboardBookmarked
        this.notification.add(_t(`Dashboard ${ updatedBookmarks ? "added to" : "removed from"} your bookmarks`),{
                                title:_t(`Bookmark ${ updatedBookmarks ? "Added" : "Removed"}`), type: 'success'});
    }



    onCreateNewChartClick() {
        let self = this;
        self.dialogService.add(FormViewDialog,{
            resModel: 'ks_dashboard_ninja.item',
            context: {
                'ks_dashboard_id': self.ks_dashboard_data.ks_dashboard_id,
                'ks_dashboard_item_type': 'ks_tile',
                'form_view_ref': 'ks_dashboard_ninja.item_form_view',
                'form_view_initial_mode': 'edit',
                'ks_set_interval': self.ks_dashboard_data.ks_set_interval,
                'ks_data_formatting':self.ks_dashboard_data.ks_data_formatting,
                'ks_form_view' : true
            },
            onRecordSaved:()=>{
                var js_id = self.env.services.action.currentController.jsId
                self.env.services.action.restore(js_id)
            },
            size: "fs",
            title: "Create New Chart"
        });
    }

    onDashboardLayoutSelect(selected_board_id){
        this.state.mode = 'layout'
        this.tempSelectedLayoutId = selected_board_id
        this.setLayoutGrid(selected_board_id);
    }

    setLayoutGrid(layout_id){
        let grid_stack = this.env.gridStackRootRef.el.gridstack
        let selected_layout_grid_config = this.ks_dashboard_data.ks_child_boards[layout_id][1];
        selected_layout_grid_config = JSON.parse(selected_layout_grid_config);
        Object.entries(selected_layout_grid_config).forEach((x,y)=>{
            grid_stack.update($(this.env.gridStackRootRef.el).find(".grid-stack-item[gs-id=" + x[0] + "]")[0],{ x:x[1]['x'], y:x[1]['y'], w:x[1]['w'], h:x[1]['h'], autoPosition:false});
        });
    }

    discardLayoutSelection(){
        this.state.mode = this.ks_dashboard_data.ks_dashboard_manager ? "manager" : "user"
        this.tempSelectedLayoutId = this.ks_dashboard_data.ks_selected_board_id
        this.setLayoutGrid(this.ks_dashboard_data.ks_selected_board_id);
    }

    _ksSetLayoutAsDefault(){
        let self = this;
        this._rpc("/web/dataset/call_kw/ks_dashboard_ninja.board/update_child_board",{
            model: 'ks_dashboard_ninja.board',
            method: 'update_child_board',
            args: ['update', self.ks_dashboard_id, {
                "ks_selected_board_id": this.tempSelectedLayoutId ? this.tempSelectedLayoutId : this.ks_dashboard_data.ks_selected_board_id,
            }],
            kwargs:{},
        }).then(function(result){
            window.location.reload();
        });
    }

    checkItemsPresence(){
        if(!this.items_length){
            this.notification.add(_t('No Items!'),{ title:_t("Create some items"), type: 'info'});
            return true;
        }
        return false;
    }

    onKsEditLayoutClick(e) {
        if(this.checkItemsPresence())   return;
        let dashboard_data = this.ks_dashboard_data
        this.tempDashboardName = dashboard_data.multi_layouts && dashboard_data.ks_child_boards ?
                                    dashboard_data.ks_child_boards[dashboard_data.ks_selected_board_id]?.[0] : dashboard_data.name
        this.env.gridStackRootRef.el.gridstack.setStatic(false);
        this.env.update_dashboard_mode('edit');
        this.env.gridStackRootRef?.el.gridstack?.enable();
        this.state.mode = "edit"
    }

    _onKsSaveLayoutClick(){
        let self = this;
        let grid_stack = this.env.gridStackRootRef.el.gridstack
        grid_stack.setStatic(true);
        let dashboard_title = this.tempDashboardName
        if (dashboard_title != false && dashboard_title != 0) {
            let model = 'ks_dashboard_ninja.board';
            let rec_id = self.ks_dashboard_data.ks_dashboard_id;

            if(this.ks_dashboard_data.multi_layouts && this.ks_dashboard_data.ks_child_boards){
                this.ks_dashboard_data.ks_child_boards[this.ks_dashboard_data.ks_selected_board_id][0] = dashboard_title;
                if (this.ks_dashboard_data.ks_selected_board_id !== 'ks_default'){
                    rec_id = parseInt(this.ks_dashboard_data.ks_selected_board_id);
                    this.env.services.orm.write("ks_dashboard_ninja.child_board", [rec_id], { 'name': dashboard_title });
                }
                else{
                    this.ks_dashboard_data.name = this.tempDashboardName;
                    this.env.services.orm.write("ks_dashboard_ninja.board", [rec_id], { 'name': dashboard_title });
                }
            }
            else{
                self.ks_dashboard_data.name = dashboard_title;
                this.env.services.orm.write("ks_dashboard_ninja.board", [rec_id], { 'name': dashboard_title });
            }
        }
        if (this.ks_dashboard_data.ks_item_data) self._ksSaveCurrentLayout();
        this.env.update_dashboard_mode('active')

        grid_stack.disable();
        grid_stack.commit();
        this.state.mode = this.ks_dashboard_data.ks_dashboard_manager ? "manager" : "user"
    }

    _ksSaveCurrentLayout() {
        let self = this;
        let grid_config = ks_get_current_gridstack_config(this.env.gridStackRootRef.el);
        let model = 'ks_dashboard_ninja.child_board';
        let rec_id = self.ks_dashboard_data.ks_gridstack_config_id;
        self.ks_dashboard_data.ks_gridstack_config = JSON.stringify(grid_config);
        if(this.ks_dashboard_data.ks_selected_board_id && this.ks_dashboard_data.ks_child_boards){
            this.ks_dashboard_data.ks_child_boards[this.ks_dashboard_data.ks_selected_board_id][1] = JSON.stringify(grid_config);
            if (this.ks_dashboard_data.ks_selected_board_id !== 'ks_default'){
                rec_id = parseInt(this.ks_dashboard_data.ks_selected_board_id)
            }
        }
        if (!isMobileOS()) {    // Do not save in Mobile view , due to column mode enable
            this._rpc("/web/dataset/call_kw/ks_dashboard_ninja.child_board/write",{
                model: model,
                method: 'write',
                args: [parseInt(rec_id), {
                    "ks_gridstack_config": JSON.stringify(grid_config)
                }],
                kwargs:{},
            })
        }
    }



    onSaveNewLayoutClick() {
        let self = this;
        let grid_stack = this.env.gridStackRootRef.el.gridstack
        grid_stack.setStatic(true);
        var dashboard_title = $('#ks_dashboard_title_input').val();
        if (dashboard_title === "") {
            self.notification.add(_t("Dashboard Name is required to save as New Layout"), { type: 'warning' });
        } else{
            if (!self.ks_dashboard_data.ks_child_boards){
                self.ks_dashboard_data.ks_child_boards = {
                    'ks_default': [ this.ks_dashboard_data.name, self.ks_dashboard_data.ks_gridstack_config ]
                }
            }
            this.ks_dashboard_data.name = dashboard_title;

            let grid_config = ks_get_current_gridstack_config(this.env.gridStackRootRef.el);
            this._rpc("/web/dataset/call_kw/ks_dashboard_ninja.board/update_child_board",{
                model: 'ks_dashboard_ninja.board',
                method: 'update_child_board',
                args: ['create', self.ks_dashboard_id, {
                    "ks_gridstack_config": JSON.stringify(grid_config),
                    "ks_dashboard_ninja_id": self.ks_dashboard_id,
                    "name": dashboard_title,
                    "ks_active": true,
                    "company_id": self.ks_dashboard_data.ks_company_id,
                }],
                kwargs : {},
            }).then(function(res_id){
                self.ks_update_child_board_value(dashboard_title, res_id, grid_config),
                window.location.reload();
            });
        }
    }

    ks_update_child_board_value(dashboard_title, res_id, grid_config){
        let self = this;
        let child_board_id = res_id.toString();
        self.ks_dashboard_data.ks_selected_board_id = child_board_id;
        let update_data = {};
        update_data[child_board_id] = [dashboard_title, JSON.stringify(grid_config)];
        self.ks_dashboard_data.ks_child_boards = Object.assign(update_data, self.ks_dashboard_data.ks_child_boards);
    }

    ksOnDashboardSettingClick(ev){
        let self = this;
        let dashboard_id = this.ks_dashboard_id;
        // TODO : Apply such functionlity that we donot have to give name of the name of the filter as string to erase cookies Also dont need to remove all cookies"
        eraseSessionItems(this.ks_dashboard_id, ['PFilter', 'PFilterDataObj', 'Filter', 'CFilter', 'FilterDateData', 'ChartFilter', 'FFilter']);
        let action = {
            name: _t('Dashboard Settings'),type: 'ir.actions.act_window',
            res_model: 'ks_dashboard_ninja.board', res_id: dashboard_id,
            domain: [],context: {'create':false},
            views: [
                [false, 'form']
            ],view_mode: 'form',target: 'new',
        }
        self.action.doAction(action).then(function(result){
        });
    }

    ksOnDashboardExportClick(){
        let self= this;
        let dashboard_id = JSON.stringify(this.ks_dashboard_id);
        this._rpc("/web/dataset/call_kw/ks_dashboard_ninja.board/ks_dashboard_export", {
            model: 'ks_dashboard_ninja.board',
            method: "ks_dashboard_export",
            args: [dashboard_id],
            kwargs: {dashboard_id: dashboard_id}
        }).then(function(result) {
                var name = "dashboard_ninja";
                var data = {"header": name, "dashboard_data":result,}
                download({
                    data: { data:JSON.stringify(data) },
                    url: '/ks_dashboard_ninja/export/dashboard_json',
                });
        });
    }

    ksOnDashboardDeleteClick(ev){
        let dashboard_id = this.ks_dashboard_id;
        let self= this;
        self.dialogService.add(ConfirmationDialog, {
            body: _t("Are you sure you want to delete this dashboard ?"),
            confirmLabel: _t("Delete Dashboard"),
            title: _t("Delete Dashboard"),
            confirm: () => {
                this._rpc("/web/dataset/call_kw/ks.dashboard.delete.wizard/ks_delete_record", {
                    model: 'ks.dashboard.delete.wizard',
                    method: "ks_delete_record",
                    args: [dashboard_id],
                    kwargs: {dashboard_id: dashboard_id}
                }).then((result)=>{
                    self.env.services.menu.reload();
                    let currentAppId = self.env.services.menu?.getCurrentApp()?.id;
                    self.env.services.menu.selectMenu(currentAppId).then(()=>{
                        self.notification.add(_t('Dashboard Deleted Successfully'),{
                            title:_t("Deleted"),
                            type: 'success',
                        });
                    });
                });
            },
        });
    }

    ksOnDashboardCreateClick(){
        var self= this;
        var action = {
            name: _t('Add New Dashboard'), type: 'ir.actions.act_window',
            res_model: 'ks.dashboard.wizard', domain: [],
            context: {}, views: [ [false, 'form']],
            view_mode: 'form', target: 'new',
        }
        self.action.doAction(action)
    }

    ksOnDashboardDuplicateClick(){
        let self= this;
        let dashboard_id = this.ks_dashboard_id;
        this._rpc('/web/dataset/call_kw/ks.dashboard.duplicate.wizard/DuplicateDashBoard', {
            model: 'ks.dashboard.duplicate.wizard', method: "DuplicateDashBoard",
            args: [this.ks_dashboard_id], kwargs: {}
        }).then((result)=>{
            self.action.doAction(result)
        });
    }

    kscreateaidashboard(){
        let self= this;
        let action = {
            name: _t('Generate Dashboard with AI'), type: 'ir.actions.act_window',
            res_model: 'ks_dashboard_ninja.ai_dashboard',domain: [],
            context: {'ks_dashboard_id': this.ks_dashboard_id},
            views: [ [false, 'form']],
            view_mode: 'form', target: 'new',
        }
        self.action.doAction(action)
    }

    kscreateaiitem(ev){
        var self= this;
        self.dialogService.add(FormViewDialog,{
            resModel: 'ks_dashboard_ninja.arti_int', title: 'Generate items with AI',
            context: {
                'ks_dashboard_id': this.ks_dashboard_id, 'ks_form_view' : true,
                'generate_dialog' : true, dialog_size: 'extra-large',
            }
        });
    }

    ksOnDashboardImportClick(){
        let self = this;
        let dashboard_id = this.ks_dashboard_id;
        this._rpc("/web/dataset/call_kw/ks_dashboard_ninja.board/ks_open_import", {
                model: 'ks_dashboard_ninja.board',
                method: 'ks_open_import',
                args: [dashboard_id],
                kwargs: {
                    dashboard_id: dashboard_id
                }
        }).then((result)=>{
            self.action.doAction(result)
        });
    }

    ksImportItemJson() {
        var self = this;
        $('.ks_input_import_item_button').click();
    }

    ksImportItem(e) {
        var self = this;
        var fileReader = new FileReader();
        fileReader.onload = function() {
            $('.ks_input_import_item_button').val('');
            self._rpc("/web/dataset/call_kw/ks_dashboard_ninja.board/ks_import_item", {
                model: 'ks_dashboard_ninja.board',
                method: 'ks_import_item',
                args: [self.ks_dashboard_id],
                kwargs: {
                    file: fileReader.result,
                    dashboard_id: self.ks_dashboard_id
                }
            }).then(function(result) {
                if (result === "Success") {
                    var js_id = self.action.currentController.jsId
                    self.action.restore(js_id)
                }
            });
        };
        fileReader.readAsText($('.ks_input_import_item_button').prop('files')[0]);
    }



    ks_gen_ai_analysis(ev){
        var self = this;
        this.state.dialog_header = false;
        var ks_items = Object.values(self.ks_dashboard_data.ks_item_data);
        var ks_items_explain = []
        var ks_rest_items = []
        if (ks_items.length>0){
            ks_items.map((item)=>{
                    ks_items_explain.push({
                        name:item.name,
                        id:item.id,
                        ks_chart_data:item.ks_chart_data?{...JSON.parse(item.ks_chart_data),...{domains:[],previous_domain:[]}}:item.ks_chart_data,
                        ks_list_view_data: typeof item.ks_list_view_data === 'string' ? JSON.parse(item.ks_list_view_data) : item.ks_list_view_data,
                        item_type:item.ks_dashboard_item_type,
                        groupedby:item.ks_chart_relation_groupby_name,
                        subgroupedby:item.ks_chart_relation_sub_groupby_name,
                        stacked_bar_chart:item.ks_bar_chart_stacked,
                        count_type:item.ks_record_count_type,
                        count:item.ks_record_count,
                        model_name:item.ks_model_display_name,
                        kpi_data:item.ks_kpi_data
                    })

            });
            this.dialogService.add(ConfirmationDialog, {
                body: _t("Do you agree that AI should be used to produce the explanation? It will take a few minutes to finish the process?"),
                title:_t("Explain with AI"),
                cancel: () => {},
                confirmLabel: _t("Confirm"),
                confirm: () => {
                    self._rpc("/web/dataset/call_kw/ks_dashboard_ninja.arti_int/ks_generate_analysis",{
                            model: 'ks_dashboard_ninja.arti_int',
                            method: 'ks_generate_analysis',
                            args: [ks_items_explain,ks_rest_items,self.ks_dashboard_id],
                            kwargs:{},
                    }).then(function(result) {
                        if (result){
                            self.action.doAction({
                                    type: "ir.actions.client",
                                    name: _t("Explain with AI"),
                                    target: "new",
                                    tag: 'ks_dashboard_ninja',
                                    params:{
                                        ks_dashboard_id: self.ks_dashboard_id,
                                        on_dialog: true,
                                        explain_ai_whole: true,
                                        explainWithAi: true,
                                        dashboard_data: self.ks_dashboard_data,
                                    },
                                     context: {
                                        dialog_size: 'extra-large'
                                     }
                                },{
                                    onClose: ()=>{
                                       return self._rpc("/web/dataset/call_kw/ks_dashboard_ninja.arti_int/ks_switch_default_dashboard",{
                                            model: 'ks_dashboard_ninja.arti_int',
                                            method: 'ks_switch_default_dashboard',
                                            args: [self.ks_dashboard_id],
                                            kwargs:{},
                                       })

                                    }
                                },
                            );
                        }
                    });
                }
            });
        }else{
            self.notification.add(_t('Please make few items to explain with AI'),{
                title:_t("Failed"),
                type: 'warning',
            });
        }
    }




};
