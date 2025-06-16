/** @odoo-module **/

import { Component, onMounted, useRef } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { FormViewDialog } from '@web/views/view_dialogs/form_view_dialog';
import { download } from "@web/core/network/download";
import { BlockUI } from "@web/core/ui/block_ui";
import { ks_get_current_gridstack_config } from '@ks_dashboard_ninja/js/ks_global_functions';
import { isMobileOS } from "@web/core/browser/feature_detection";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";


export class KsItemButton extends Component{
    static props = { item_data : { type: Object, optional:true },
                     item_classes : { type: String, optional:true },
                     itemRootRef : { type: Object },
                    }
    static template = "ks_dashboard_ninja.ks_chart_buttons";

    setup(){
        this.common_classes = 'ks_dashboard_item_button_container ks_dropdown_container ks_dashboard_item_header ks_dashboard_item_header_hover chart_button_container d-flex '
        this.ks_company = this.env.services.company.currentCompany.name
        this.isMobile = isMobileOS()
        this.item_data = this.props.item_data
        this.ks_button_color = this._ks_get_rgba_format(this.item_data.ks_button_color)
        this.id = this.props.item_data.id
        this.rootRef = useRef('rootRef')
        this.ksChartColorOptions = ["default", "dark", "moonrise", "material"]
        this.chart_list = ['ks_bar_chart', 'ks_horizontalBar_chart', 'ks_line_chart', 'ks_area_chart', 'ks_pie_chart',
                            'ks_doughnut_chart', 'ks_polarArea_chart', 'ks_radialBar_chart', 'ks_scatter_chart', 'ks_funnel_chart',
                            'ks_bullet_chart', 'ks_flower_view', 'ks_radar_view']
        this.isExportListVisible = [ ...this.chart_list, 'ks_map_view', 'ks_list_view'].includes(this.item_data.ks_dashboard_item_type)
        this.mailChatService = useService("mail.chat_window");
        this.threadService = useService("mail.thread");
        this.showButtons = !this.env.inDialog
        this.selectedDashboardId = this.item_data.ks_dashboard_list[0]['id']

        this.setItemDescription(this.item_data.ks_info)
    }

    _ks_get_rgba_format(val){
        let rgba = val.split(',')[0].match(/[A-Za-z0-9]{2}/g);
        rgba = rgba.map(function(v) {
            return parseInt(v, 16)
        }).join(",");
        return "rgba(" + rgba + "," + val.split(',')[1] + ")";
    }

    setItemDescription(item_description){
        let item_description_list = item_description.replace?.(/\\n/g, '\n').split?.('\n').filter(element => element !== '');
        this.item_data.ks_info = item_description_list?.join?.(' ') ?? false
        this.ks_item_description_list = item_description_list ?? false
    }

    handleDropdowns(ev){
        let targetDropdown = ev.target.closest('.dropdown-toggle')
        this.rootRef.el.querySelectorAll('.dropdown-toggle').forEach((dropdown) => {
            targetDropdown !== dropdown ?  Dropdown.getInstance(dropdown)?.hide() : ''
        })
    }

    onEditItemTypeClick() {
        var self = this;
        self.env.services.dialog.add(FormViewDialog,{
            resModel: 'ks_dashboard_ninja.item',
            title: 'Edit Chart',
            resId : self.id,
            context: {
                'form_view_ref': 'ks_dashboard_ninja.item_form_view',
                'form_view_initial_mode': 'edit',
                'ks_form_view' :true
            },
            onRecordSaved:()=>{
                var js_id = self.env.services.action.currentController.jsId
                self.env.services.action.restore(js_id)
            },
            onRecordDiscarded:()=>{
            },
            size: 'fs'
        });
    }

    async ksChartExportXlsCsv(e) {
        let chart_id = this.id;
        let name = this.item_data.name;
        let context = this.env.getContext();
        let data = {}
        if (this.item_data.ks_dashboard_item_type === 'ks_list_view'){
            let params = this.env.ksGetParamsForItemFetch(chart_id);
            data = {
                "header": name,
                "chart_data": typeof this.item_data.ks_list_view_data === 'string' ? this.item_data.ks_list_view_data : JSON.stringify(this.item_data.ks_list_view_data),
                "ks_item_id": chart_id,
                "ks_export_boolean": true,
                "context": context,
                'params': params,
            }
        }else{
             data = {
                "header": name,
                "chart_data": this.item_data.ks_chart_data,
             }
        }
        const blockUI = new BlockUI();
        await download({
            url: '/ks_dashboard_ninja/export/' + e.currentTarget.dataset.format,
            data: {
                data: JSON.stringify(data)
            },
            complete: () => unblockUI,
            error: (error) => self.call('crash_manager', 'rpc_error', error),
        });
    }

    ksChartExportPdf (e){
        var self = this;
        var chart_id = this.id;
        var name = this.item_data.name;
        var base64_image;
        base64_image = $($(e.target).parentsUntil(".grid-stack-item").slice(-1)[0]).find('.ks_chart_card_body')[0]
        var $ks_el = $($($(self.props.itemRootRef.el).find(".grid-stack-item[gs-id=" + chart_id + "]")).find('.ks_chart_card_body'));
        var ks_height = $ks_el.height()
        html2canvas(base64_image, {useCORS: true, allowTaint: false}).then(function(canvas){
            var ks_image = canvas.toDataURL("image/png");
            var ks_image_def = {
            content: [{
                    image: ks_image,
                    width: 500,
                    height: ks_height > 750 ? 750 : ks_height,
                    }],
            images: {
                bee: ks_image
            }
        };
        pdfMake.createPdf(ks_image_def).download(name + '.pdf');
        })

    }

    ksChartExportimage(e){
        var self = this;
        var chart_id = this.id;
        var name = this.item_data.name;
        var base64_image
        base64_image = $($(e.target).parentsUntil(".grid-stack-item").slice(-1)[0]).find(".ks_chart_card_body")[0]
        html2canvas(base64_image,{useCORS: true, allowTaint: false}).then(function(canvas){
            var ks_image = canvas.toDataURL("image/png");
            const link = document.createElement('a');
            link.href =  ks_image;
            link.download = name + 'png'
            document.body.appendChild(link);
            link.click()
            document.body.removeChild(link);
        })

    }

    async ksItemExportJson(e) {
        var itemId = this.id;
        var name = this.item_data.name;
        var data = { 'header': name, item_id: itemId, }
        const blockUI = new BlockUI();
        await download({
            url: '/ks_dashboard_ninja/export/item_json',
            data: { data: JSON.stringify(data) },
            complete: () => unblockUI,
            error: (error) => self.call('crash_manager', 'rpc_error', error),
        });
    }

    async openChatWizard(ev){
        ev.stopPropagation();
        let internal_chat_thread;
        let channelId = await this.env.services.rpc("/web/dataset/call_kw/discuss.channel/getId",{
            model: 'discuss.channel',
            method: 'ks_chat_wizard_channel_id',
            args: [[]],
            kwargs:{
                item_id: this.id,
                dashboard_id: this.item_data.ks_dashboard_id,
                dashboard_name: this.item_data.ks_dashboard_name,
                item_name: this.item_data.name,
            }
        })

        // FIXME : Dont close all chat popover windows . only close charts visible popovers


        this.mailChatService.visible?.forEach?.( (visibleChatWindow) => {
            this.mailChatService.close(visibleChatWindow)
        })

        //
        if(channelId)   internal_chat_thread = this.threadService.getThread("discuss.channel", channelId)
        if(internal_chat_thread){
            if(internal_chat_thread.name)   internal_chat_thread.name = this.item_data.ks_dashboard_name + ' - ' + this.item_data.name
            this.mailChatService?.open(internal_chat_thread)
        }

    }

    onKsDuplicateItemClick(e) {
        var self = this;
        var ks_item_id = this.id;
        var dashboard_id = parseInt(this.selectedDashboardId);
        var dashboard_name = this.item_data.ks_dashboard_list.filter( (dashboard) => dashboard.id === dashboard_id)[0]?.name;
        this.env.services.rpc("/web/dataset/call_kw/ks_dashboard_ninja.item/copy",{
            model: 'ks_dashboard_ninja.item',
            method: 'copy',
            args: [ks_item_id, {
                'ks_dashboard_ninja_board_id': dashboard_id
            }],
            kwargs:{},
        }).then(function(result) {
            self.env.services.notification.add(_t('Selected item is duplicated to ' + dashboard_name + ' .'),{
                title:_t("Item Duplicated"), type: 'success', });
            var js_id = self.env.services.action.currentController.jsId
            self.env.services.action.restore(js_id)
        })
    }

    onKsMoveItemClick(e) {
        let self = this;
        let dashboard_id = parseInt(this.selectedDashboardId);
        let dashboard_name = this.item_data.ks_dashboard_list.filter( (dashboard) => dashboard.id === dashboard_id)[0]?.name;
        this.env.services.rpc("/web/dataset/call_kw/ks_dashboard_ninja.item/write",{
            model: 'ks_dashboard_ninja.item',
            method: 'write',
            args: [this.id, {
                'ks_dashboard_ninja_board_id': dashboard_id
            }],
            kwargs:{}
        }).then(function(result) {
            self.env.services.notification.add(_t('Selected item is moved to ' + dashboard_name + ' .'), {
                title:_t("Item Moved"), type: 'success', });
            var js_id = self.env.services.action.currentController.jsId
            self.env.services.action.restore(js_id)
        });
    }

    onKsDeleteItemClick(e) {
        let self = this;
        let item = $($(e.currentTarget).parentsUntil('.grid-stack').slice(-1)[0])
        this.env.services.dialog.add(ConfirmationDialog, {
            body: _t("Are you sure that you want to remove this item?"),
            confirmLabel: _t("Delete Item"),
            title: _t("Delete Dashboard Item"),
            confirm: () => {
                self.ks_delete_item(self.id , item);
            },
            cancel: () => {},
        });
    }

    ks_delete_item(id, item) {
        let self = this;
        let dashboard_data = self.env.getDashboardDataAsObj(['ks_item_data'])
        self.env.services.rpc("/web/dataset/call_kw/ks_dashboard_ninja.item/unlink", {
            model: 'ks_dashboard_ninja.item',
            method: 'unlink',
            args: [id],
            kwargs:{}
        }).then(function(result) {
                    // Clean Item Remove Process. // TODO
//                self.ks_remove_update_interval(); // IMPORTANT
            delete self.props.item_data;
            self.env.gridStackRootRef.el.gridstack?.removeWidget(item);
            if (Object.keys(dashboard_data.ks_item_data).length > 0) {
                self._ksSaveCurrentLayout();
            }
            let js_id = self.env.services.action.currentController.jsId
            self.env.services.action.restore(js_id)
        });
    }

    _ksSaveCurrentLayout() {
        let self = this;
        let grid_config = ks_get_current_gridstack_config(this.env.gridStackRootRef.el);
        let dashboard_data = self.env.getDashboardDataAsObj(['ks_gridstack_config_id'])
        let model = 'ks_dashboard_ninja.child_board';
        let rec_id = dashboard_data.ks_gridstack_config_id;

        if (!isMobileOS()) {
            this.env.services.rpc("/web/dataset/call_kw/ks_dashboard_ninja.child_board/write",{
                model: model,
                method: 'write',
                args: [rec_id, {
                    "ks_gridstack_config": JSON.stringify(grid_config)
                }],
                kwargs:{},
            })
        }
    }

    ksRenderChartColorOptions(e) {
        let self = this;
//            FIXME : Correct this later.
            this.__owl__.parent.component.ksRenderChartColorOptions(e);
    }
}
