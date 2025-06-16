/** @odoo-module **/
import { Component, onWillStart, useState ,useEffect,onMounted, onPatched, onWillUpdateProps,useRef, onWillUnmount, markup, onError } from "@odoo/owl";
import { onAudioEnded, convert_data_to_utc } from '@ks_dashboard_ninja/js/ks_global_functions';
import { KsItemButton } from '@ks_dashboard_ninja/components/chart_buttons/chart_buttons';
import { jsonrpc } from "@web/core/network/rpc_service";
import { useBus, useService } from "@web/core/utils/hooks";
import { formatFloat } from "@web/core/utils/numbers";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { localization } from "@web/core/l10n/localization";
import {formatDate,formatDateTime} from "@web/core/l10n/dates";
import { parseDateTime, parseDate } from "@web/core/l10n/dates";
import { renderToElement, renderToString } from "@web/core/utils/render";
import { isMobileOS } from "@web/core/browser/feature_detection";
import { ks_render_graphs, ksrenderfunnelchart, ksrendermapview } from "@ks_dashboard_ninja/js/charts_render_global_functions";
import { Domain } from "@web/core/domain";
import { domainFromTree } from "@web/core/tree_editor/condition_tree";
import { condition, connector } from "@web/core/tree_editor/condition_tree";

export class Ksdashboardgraph extends Component{
    setup(){
        this.markup = markup;
        this.chart_container = {};
        this.dialogService = useService("dialog");
        this.actionService = useService("action");
        this._rpc = useService("rpc");
        this.state = useState({item_data:"",list_view_data:"", update_chart: 0})
        onMounted(() => this._update_view());
        onPatched(() => this.update_list_view());
        this.item = this.props.item
        this.item.ksIsDashboardManager = this.props.dashboard_data.ks_dashboard_manager
        this.item.ks_dashboard_list = this.props.dashboard_data.ks_dashboard_list
        this.ks_dashboard_id = this.props.item.ks_dashboard_id
        this.ks_dashboard_data = this.props.dashboard_data
        if (this.item.ks_dashboard_item_type == 'ks_list_view'){
            this.prepare_list()
        }else{
            this.prepare_item(this.item);
        }
        this.ks_gridstack_container = useRef("ks_gridstack_container");
        this.aiAudioRef = useRef("aiAudioRef");
        this.ks_list_view = useRef("ks_list_view");

        var update_interval = this.props.dashboard_data.ks_set_interval
        this.ks_ai_analysis = this.ks_dashboard_data.ks_ai_explain_dash
        if (this.item.ks_ai_analysis && this.item.ks_ai_analysis){
            var ks_analysis = this.item.ks_ai_analysis.split('ks_gap')
            this.ks_ai_analysis_1 = ks_analysis[0]
            this.ks_ai_analysis_2 = ks_analysis[1]
        }


         onWillUpdateProps((nextprops)=>{
            if (nextprops.itemsToUpdateList.length){
                if (nextprops.itemsToUpdateList?.includes(this.item.id)){
                    this.ksFetchUpdateItem(this.item.id, this.ks_dashboard_id,  nextprops.dashboard_data.context)
                }
            }
        })

        onWillUnmount( () => {
            this.aiAudioRef.el?.removeEventListener('ended', onAudioEnded)
        })
    }

    get isMobile() {
        return isMobileOS();
    }

    ksFetchUpdateItem(item_id, dash_id, context, domain = this.env.ksGetParamsForItemFetch(item_id)) {
            this.root?.dispose();
            this.env.services.ui.block();
            var self = this;
            context = self.env.getContext();
            jsonrpc("/web/dataset/call_kw",{
                model: 'ks_dashboard_ninja.board',
                method: 'ks_fetch_item',
                args: [
                    [parseInt(item_id)], dash_id,domain
                ],
                kwargs: { context },
            })
            .then((new_item_data) => {
                if(new_item_data[item_id].ks_list_view_data){
                    new_item_data[item_id].ks_list_view_data = convert_data_to_utc(new_item_data[item_id].ks_list_view_data)
                }
                this.ks_dashboard_data.ks_item_data[item_id] = new_item_data[item_id];
                this.item = this.ks_dashboard_data.ks_item_data[item_id] ;
                // done this to render updated items on play button
                this.__owl__.parent.component.ks_dashboard_data.ks_item_data[this.item.id] = new_item_data[item_id]
                if (this.item.ks_dashboard_item_type =="ks_funnel_chart"){
                    $(this.ks_gridstack_container.el).find(".card-body").remove()
                    ksrenderfunnelchart.bind(this)($(this.ks_gridstack_container.el),this.item, 'dashboard_view');
                }else if(this.item.ks_dashboard_item_type =="ks_list_view"){
                    this.prepare_list()
                     if (this.intial_count < this.item.ks_pagination_limit ) {
                        $(this.ks_list_view.el).find('.ks_load_next').addClass('ks_event_offer_list');
                    }else{
                        $(this.ks_list_view.el).find('.ks_load_next').removeClass('ks_event_offer_list');
                    }

                }else if(this.item.ks_dashboard_item_type == ("ks_map_view")){
                    $(this.ks_gridstack_container.el).find(".card-body").remove()
                    ksrendermapview.bind(this)($(this.ks_gridstack_container.el),this.item, 'dashboard_view')
                }else{
                    $(this.ks_gridstack_container.el).find(".card-body").remove()
                    ks_render_graphs.bind(this)($(this.ks_gridstack_container.el),this.item, this.props.dashboard_data.zooming_enabled, 'dashboard_view')
                }
                this.env.services.ui.unblock();
            });

        }

    _update_view(){
        let self = this
        if(this.item.ks_dashboard_item_type == 'ks_list_view'){
            if (this.item.ks_pagination_limit < this.intial_count) {
            $(this.ks_list_view.el).find('.ks_load_next').addClass('ks_event_offer_list');
        }
        if (this.intial_count < this.item.ks_pagination_limit ) {
             $(this.ks_list_view.el).find('.ks_load_next').addClass('ks_event_offer_list');
        }
        if (this.item.ks_record_data_limit === this.item.ks_pagination_limit){
                $(this.ks_list_view.el).find('.ks_load_next').addClass('ks_event_offer_list');
        }
        if (this.intial_count == 0){
             $(this.ks_list_view.el).find('.ks_pager').addClass('d-none');
        }
        if (this.item.ks_pagination_limit==0){
             $(this.ks_list_view.el).find('.ks_pager_name').addClass('d-none');
        }
        if (this.item.ks_data_calculation_type === 'query' || this.item.ks_list_view_type === "ungrouped"){
            $('.ks_list_canvas_click').removeClass('ks_list_canvas_click');
        }
        }else{
         if (this.item.ks_data_calculation_type === 'query'){
                $(this.ks_gridstack_container.el).find(".ks_dashboard_item_chart_info").addClass('d-none');
          }
        $(this.ks_gridstack_container.el).addClass('ks_dashboarditem_id');
        $(this.ks_gridstack_container.el).find(".ks_dashboard_item_button_container").addClass("ks_funnel_item_container")
        if (this.item.ks_dashboard_item_type =="ks_funnel_chart"){
                ksrenderfunnelchart.bind(this)($(this.ks_gridstack_container.el),this.item, 'dashboard_view')
        }else if(this.item.ks_dashboard_item_type == ("ks_map_view")){
            ksrendermapview.bind(this)($(this.ks_gridstack_container.el),this.item, 'dashboard_view')
        }else{
            ks_render_graphs.bind(this)($(this.ks_gridstack_container.el),this.item, this.props.dashboard_data.zooming_enabled, 'dashboard_view')
        }
        }
        this.aiAudioRef.el?.addEventListener('ended', onAudioEnded)

    }
    update_list_view(){
        if(this.item.ks_dashboard_item_type == 'ks_list_view'){
            if (this.item.ks_pagination_limit < this.intial_count) {
            $(this.ks_list_view.el).find('.ks_load_next').addClass('ks_event_offer_list');
        }
        if (this.intial_count < this.item.ks_pagination_limit ) {
             $(this.ks_list_view.el).find('.ks_load_next').addClass('ks_event_offer_list');
        }
        if (this.item.ks_record_data_limit === this.item.ks_pagination_limit){
                $(this.ks_list_view.el).find('.ks_load_next').addClass('ks_event_offer_list');
        }
        if (this.intial_count == 0){
             $(this.ks_list_view.el).find('.ks_pager').addClass('d-none');
        }
        if (this.intial_count != 0){
             $(this.ks_list_view.el).find('.ks_pager').removeClass('d-none');
        }
        if (this.item.ks_pagination_limit==0){
             $(this.ks_list_view.el).find('.ks_pager_name').addClass('d-none');
        }
        if (this.item.ks_data_calculation_type === 'query' || this.item.ks_list_view_type === "ungrouped"){
            $('.ks_list_canvas_click').removeClass('ks_list_canvas_click');
        }
    }
    }

    prepare_list() {
        var self = this;
        if (this.item.ks_info){
            var ks_description = this.item.ks_info.replace?.(/\\n/g, '\n').split?.('\n');
            var ks_description = ks_description.filter(element => element !== '')
        }else {
            var ks_description = false;
        }
        if (typeof(this.item.ks_list_view_data) == 'string'){
            var list_view_data = JSON.parse(this.item.ks_list_view_data)
        }else{
             var list_view_data = this.item.ks_list_view_data
        }
        var data_rows = list_view_data.data_rows
        var length = data_rows ? data_rows.length: false;
        var item_id = this.item.id
        this.ks_info = ks_description?.join?.(' ') ?? false;
        this.ks_chart_title = this.item.name
        this.ks_breadcrumb = this.item.ks_action_name
        this.item_id = item_id
        this.ksIsDashboardManager= self.ks_dashboard_data.ks_dashboard_manager,
        this.ksIsUser = true,
        this.ks_dashboard_list = self.ks_dashboard_data.ks_dashboard_list,
        this.count = '1-' + length
        this.offset = 1
        this.intial_count = length
        this.ks_company= this.item.ks_company
        this.calculation_type = this.ks_dashboard_data.ks_item_data[this.item_id].ks_data_calculation_type
        this.self = this

        if (this.item.ks_list_view_type === "ungrouped" && list_view_data) {
            if (list_view_data.date_index) {
                var index_data = list_view_data.date_index;
                for (var i = 0; i < index_data.length; i++) {
                    for (var j = 0; j < list_view_data.data_rows.length; j++) {
                        var index = index_data[i]
                        var date = list_view_data.data_rows[j]["data"][index]
                        if (date) {
                            if( list_view_data.fields_type[index] === 'date'){
                             let parsedDate = parseDate(date,{format: localization.dateFormat});
                                list_view_data.data_rows[j]["data"][index] = formatDate(parsedDate, { format: localization.dateFormat })
                            } else{
                            let parsedDate = parseDateTime(date,{format: localization.dateTimeFormat});
                                list_view_data.data_rows[j]["data"][index] = formatDateTime(parsedDate, { format: localization.dateTimeFormat })
                            }
                        }else{
                        }
                    }
                }
            }
        }
        if (list_view_data) {
            for (var i = 0; i < list_view_data.data_rows.length; i++) {
                for (var j = 0; j < list_view_data.data_rows[0]["data"].length; j++) {
                    if (typeof(list_view_data.data_rows[i].data[j]) === "number" || list_view_data.data_rows[i].data[j]) {
                        if (typeof(list_view_data.data_rows[i].data[j]) === "number") {
                            list_view_data.data_rows[i].data[j] = formatFloat(list_view_data.data_rows[i].data[j], Float64Array, {digits:[0, self.item.ks_precision_digits]})
                        }
                    } else {
                    }
                }
            }
        }
        this.state.list_view_data = list_view_data
        this.list_type = this.item.ks_list_view_type
        this.ks_pager = true
        this.tmpl_list_type = self.ks_dashboard_data.ks_item_data[this.item_id].ks_list_view_type
        this.isDrill = this.ks_dashboard_data.ks_item_data[this.item_id]['isDrill']
        this.ks_show_records = this.item.ks_show_records
    }

    prepare_item(item) {
     var self = this;
     var isDrill = item.isDrill ? item.isDrill : false;
     this.chart
     var chart_id = item.id;
     this.ksColorOptions = ["default","dark","moonrise","material"]
     var funnel_title = item.name;
     if (item.ks_info){
        var ks_description = item.ks_info.replace?.(/\\n/g, '\n').split?.('\n');
        var ks_description = ks_description.filter(element => element !== '')
     }else {
        var ks_description = false;
     }

     this.ks_chart_title= funnel_title,
     this.ksIsDashboardManager= self.ks_dashboard_data.ks_dashboard_manager,
     this.ksIsUser = true,
     this.ks_dashboard_list = self.ks_dashboard_data.ks_dashboard_list,
     this.chart_id = chart_id,
     this.ks_info = ks_description?.join?.(' ') ?? false,
     this.ksChartColorOptions = this.ksColorOptions,
     this.ks_company = item.ks_company,
     this.ks_dashboard_item_type = item.ks_dashboard_item_type,
     this.ks_breadcrumb = item.ks_action_name
    }

     onChartCanvasClick(evt, column_index = false, row_data = false, column_field_type = false) {
        var self = this;
        this.ksUpdateDashboard = {};
        if(this.env.inDialog) return ;
        var item_id = $(evt.target).parent().data().itemId;
        var chart_title = '#'+this.item.name
        var item_data = self.ks_dashboard_data.ks_item_data[item_id]
        let isGroupedList = self.ks_dashboard_data.ks_item_data[item_id].ks_list_view_type === 'grouped'
        if (self.ks_dashboard_data.ks_item_data[item_id].max_sequnce && isGroupedList) {

            var sequence = item_data.sequnce ? item_data.sequnce : 0

            var domain = $(evt.target).parent().data().domain;

            if ($(evt.target).parent().data().last_seq !== sequence) {
                self._rpc("/web/dataset/call_kw/ks_dashboard_ninja.item/ks_fetch_drill_down_data",{
                    model: 'ks_dashboard_ninja.item',
                    method: 'ks_fetch_drill_down_data',
                    args: [item_id, domain, sequence],
                    kwargs : {},
                }).then((result) => {
                    if (result.ks_list_view_data) {
                        var chart_id_name = '#item'+'_' +'-1'
                        var id_name = '#'+result.ks_action_name + '_' + (result.sequence-1)
                        if (self.ks_dashboard_data.ks_item_data[item_id].domains) {
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_list_view_data).previous_domain;
                        } else {
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'] = {}
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_list_view_data).previous_domain;
                        }
                        self.ks_dashboard_data.ks_item_data[item_id]['isDrill'] = true;
                        self.ks_dashboard_data.ks_item_data[item_id]['sequnce'] = result.sequence;
                        self.ks_dashboard_data.ks_item_data[item_id]['ks_list_view_data'] = result.ks_list_view_data;
                        self.ks_dashboard_data.ks_item_data[item_id]['ks_list_view_type'] = result.ks_list_view_type;
                        self.ks_dashboard_data.ks_item_data[item_id]['ks_dashboard_item_type'] = 'ks_list_view';
                        self.ks_dashboard_data.ks_item_data[item_id]['sequnce'] = result.sequence;
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_more_action").addClass('d-none');
                        $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".ks_chart_heading").addClass("d-none")
                        $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".ks_list_view_heading").addClass("d-none")
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").empty();
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(chart_id_name).removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_search_plus").addClass('d-none')
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_search_minus").addClass('d-none')
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(id_name).removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_pager").addClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_action_export").addClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_quick_edit_action_popup").removeClass('d-sm-block ');

                         var item_data = self.ks_dashboard_data.ks_item_data[item_id]
                         var list_view_data = JSON.parse(item_data['ks_list_view_data'])

                        var $container = renderToElement('ks_dashboard_ninja.ks_new_list_view_table',{
                        list_view_data,item_id:self.item_id,self, markup, state: { list_view_data }
                        })
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").append($container);

                    } else {
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_more_action").addClass('d-none');
                        self.ks_dashboard_data.ks_item_data[item_id]['ks_chart_data'] = result.ks_chart_data;
                        self.ks_dashboard_data.ks_item_data[item_id]['sequnce'] = result.sequence;
                        self.ks_dashboard_data.ks_item_data[item_id]['ks_dashboard_item_type'] = result.ks_chart_type;
                        self.ks_dashboard_data.ks_item_data[item_id]['isDrill'] = true;
                        var chart_id_name = '#item'+'_' +'-1'
                        var id_name = '#'+result.ks_action_name + '_' + (result.sequence-1)
                        if (self.ks_dashboard_data.ks_item_data[item_id].domains) {
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_chart_data).previous_domain;
                        } else {
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'] = {}
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_chart_data).previous_domain;
                        }
                        $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".ks_list_view_heading").addClass("d-none")
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(chart_id_name).removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(id_name).removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_chart_info").removeClass('d-none')
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_color_option").removeClass('d-none')
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_search_plus").addClass('d-none')
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_search_minus").addClass('d-none')
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_pager").addClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_quick_edit_action_popup").removeClass('d-sm-block ');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_action_export").addClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").empty();
                        var item_data = self.ks_dashboard_data.ks_item_data[item_id]
                        if(item_data.ks_dashboard_item_type == 'ks_funnel_chart'){
                            $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".card-body").remove();
                            ksrenderfunnelchart.bind(this)($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]"), item_data, 'dashboard_view');
                        }else{
                        $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".card-body").remove();
                            ks_render_graphs.bind(this)($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]"), item_data, self.props.dashboard_data.zooming_enabled, 'dashboard_view');
                        }

                    }
                });
            }
        }
        else{

        }
        evt.stopPropagation();
     }



     async onChartCanvasClick_funnel(evt, item_id, item){
        var self = this;
        if(this.env.inDialog || self.env.mode === 'edit') return ;
        this.ksUpdateDashboard = {};
        var domain = [];
        var partner_id;
        var final_active;
        var index;
        var item_data = self.ks_dashboard_data.ks_item_data[item_id];
        var groupBy = JSON.parse(item_data["ks_chart_data"])['groupby'];
        var labels = JSON.parse(item_data["ks_chart_data"])['labels'];
        var domains = JSON.parse(item_data["ks_chart_data"])['domains'];
        var sequnce = item_data.sequnce ? item_data.sequnce : 0;
        var chart_title = '#'+item.name
        if (evt.target.dataItem){
            var activePoint = evt.target.dataItem.dataContext;
        }
        if (activePoint) {
            if (activePoint.category){
                for (let i=0 ; i<labels.length ; i++){
                    if (labels[i] == activePoint.category){
                        index = i
                    }
                }
                domain = domains[index]
            }
            else if (activePoint.stage){
                for (let i=0 ; i<labels.length ; i++){
                    if (labels[i] == activePoint.stage){
                        index = i
                    }
                }
                domain = domains[index]
            }
            if (item_data.max_sequnce != 0 && sequnce < item_data.max_sequnce) {
                self._rpc("/web/dataset/call_kw/ks_dashboard_ninja.item/ks_fetch_drill_down_data",{
                    model: 'ks_dashboard_ninja.item',
                    method: 'ks_fetch_drill_down_data',
                    args: [item_id, domain, sequnce],
                    kwargs : {},
                }).then((result) => {
                    self.ks_dashboard_data.ks_item_data[item_id]['sequnce'] = result.sequence;
                    self.ks_dashboard_data.ks_item_data[item_id]['isDrill'] = true;
                    if (result.ks_chart_data) {

                        var chart_id_name = '#item'+'_' +'-1'
                        var id_name = '#'+result.ks_action_name + '_' + (result.sequence-1)
                        self.ks_dashboard_data.ks_item_data[item_id]['ks_dashboard_item_type'] = result.ks_chart_type;
                        self.ks_dashboard_data.ks_item_data[item_id]['ks_chart_data'] = result.ks_chart_data;
                        if (self.ks_dashboard_data.ks_item_data[item_id].domains) {
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_chart_data).previous_domain;
                        } else {
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'] = {}
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_chart_data).previous_domain;
                        }
                        $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".ks_chart_heading").addClass("d-none")
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(chart_id_name).removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(id_name).removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_chart_info").removeClass('d-none')
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_color_option").removeClass('d-none')
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_quick_edit_action_popup").removeClass('d-sm-block ');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_more_action").addClass('d-none');

                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").empty();
                        var item_data = self.ks_dashboard_data.ks_item_data[item_id]
                        if(item_data.ks_dashboard_item_type == 'ks_funnel_chart'){
                            $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".card-body").remove();
                            ksrenderfunnelchart.bind(this)($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]"),item_data, 'dashboard_view');
                        }else{
                            $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".card-body").remove();
                            ks_render_graphs.bind(this)($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]"), item_data, self.props.dashboard_data.zooming_enabled, 'dashboard_view');
                        }
                    } else {
                        if ('domains' in self.ks_dashboard_data.ks_item_data[item_id]) {
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_list_view_data).previous_domain;
                        } else {
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'] = {}
                            self.ks_dashboard_data.ks_item_data[item_id]['domains'][result.sequence] = JSON.parse(result.ks_list_view_data).previous_domain;
                        }
                        var chart_id_name = '#item'+'_' +'-1'
                        var id_name = '#'+result.ks_action_name + '_' + (result.sequence-1)
                        self.ks_dashboard_data.ks_item_data[item_id]['isDrill'] = true;
                        self.ks_dashboard_data.ks_item_data[item_id]['sequnce'] = result.sequence;
                        self.ks_dashboard_data.ks_item_data[item_id]['ks_list_view_data'] = result.ks_list_view_data;
                        self.ks_dashboard_data.ks_item_data[item_id]['ks_list_view_type'] = result.ks_list_view_type;
                        self.ks_dashboard_data.ks_item_data[item_id]['ks_dashboard_item_type'] = 'ks_list_view';

                        $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".ks_chart_heading").addClass("d-none")
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(chart_id_name).removeClass('d-none');

                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(id_name).removeClass('d-none');

                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_chart_info").addClass('d-none')
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_color_option").addClass('d-none')
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").empty();
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_quick_edit_action_popup").removeClass('d-sm-block ');

                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_more_action").addClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").addClass('table-responsive');
                        var item_data = self.ks_dashboard_data.ks_item_data[item_id]
                        self.item = item_data
                        self.prepare_list();
                        var list_view_data = JSON.parse(item_data['ks_list_view_data'])

                        var $container = renderToElement('ks_dashboard_ninja.ks_new_list_view_table',{
                        list_view_data,item_id:self.item_id,self, markup, state: { list_view_data }
                        })

                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").append($container);
                    }
                });
            } else {
                if (item_data.action) {
                    var action = Object.assign({}, item_data.action);
                    if (action.view_mode.includes('tree')) action.view_mode = action.view_mode.replace('tree', 'list');
                    for (var i = 0; i < action.views.length; i++) action.views[i][1].includes('tree') ? action.views[i][1] = action.views[i][1].replace('tree', 'list') : action.views[i][1];
                    action['domain'] = domain || [];
                    action['search_view_id'] = [action.search_view_id, 'search']
                } else {
                    var action = {
                        name: _t(item_data.name),
                        type: 'ir.actions.act_window',
                        res_model: item_data.ks_model_name,
                        domain: domain || [],
                        context: {
                            'group_by': groupBy ? groupBy:false ,
                        },
                        views: [
                            [false, 'list'],
                            [false, 'form']
                        ],
                        view_mode: 'list',
                        target: 'current',
                    }
                }
                if (item_data.ks_show_records && action) {

                    self.actionService.doAction(action, {
                        on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                    });
                }
            }
        }
     }

     ksOnDrillUp(e) {
        var self = this;
        var item_id = e.currentTarget.dataset.itemId;
        var item_data = self.ks_dashboard_data.ks_item_data[item_id];
        var domain;
        var chart_name = '#'+item_data.name
        var sequence = parseInt(e.currentTarget.dataset.sequence)
        var chart_id_name =  '#item'+'_' +'-1'
        if(item_data) {

            if ('domains' in item_data) {
                domain = item_data['domains'][sequence+1] ? item_data['domains'][sequence+1] : []
                var sequnce = sequence;
                if (sequnce >= 0) {
                    self._rpc("/web/dataset/call_kw/ks_dashboard_ninja.item/ks_fetch_drill_down_data",{
                        model: 'ks_dashboard_ninja.item',
                        method: 'ks_fetch_drill_down_data',
                        args: [item_id, domain, sequnce],
                        kwargs:{}
                    }).then((result) => {
                        self.ks_dashboard_data.ks_item_data[item_id]['ks_chart_data'] = result.ks_chart_data;
                        self.ks_dashboard_data.ks_item_data[item_id]['sequnce'] = result.sequence;
                        var id_name = '#'+result.ks_action_name + '_' + sequence;
                        var ks_breadcrumb_elements  = $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(id_name).nextAll();
                        if (result.ks_chart_type) {
                            self.ks_dashboard_data.ks_item_data[item_id]['ks_dashboard_item_type'] = result.ks_chart_type;
                            self.item.ks_dashboard_item_type = result.ks_chart_type
                        }
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").removeClass('d-none');
                        $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").empty();
                        if (result.ks_chart_data) {
                            var item_data = self.ks_dashboard_data.ks_item_data[item_id];
                            ks_breadcrumb_elements.each(function(index,item){
                                $(item).addClass("d-none")
                            })
                            $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_chart_info").removeClass('d-none')
                            $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_color_option").removeClass('d-none')
                            $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".card-body").remove()
                            if (result.ks_chart_type == "ks_funnel_chart"){
                                ksrenderfunnelchart.bind(this)($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]"),item_data, 'dashboard_view');
                            }else{
                                ks_render_graphs.bind(this)($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]"), item_data, self.props.dashboard_data.zooming_enabled, 'dashboard_view');
                            }
                        } else {
                            self.ks_dashboard_data.ks_item_data[item_id]['ks_list_view_data'] = result.ks_list_view_data;
                            self.ks_dashboard_data.ks_item_data[item_id]['ks_list_view_type'] = result.ks_list_view_type;
                            self.ks_dashboard_data.ks_item_data[item_id]['ks_dashboard_item_type'] = 'ks_list_view';
                            self.item.ks_dashboard_item_type = 'ks_list_view';
                            var item_data = self.ks_dashboard_data.ks_item_data[item_id]
                            ks_breadcrumb_elements.each(function(index,item){
                                $(item).addClass("d-none")
                            })
                            self.prepare_list(item_data);
                            $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_pager").addClass('d-none');
                            $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_chart_info").addClass('d-none')
                            $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_color_option").addClass('d-none')
                            var list_view_data = JSON.parse(item_data['ks_list_view_data'])

                            var $container = renderToElement('ks_dashboard_ninja.ks_new_list_view_table',{
                            list_view_data,item_id:self.item_id,self, markup, state: { list_view_data }
                            })
                            $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".card-body").append($container);
                        }

                    });

                } else {
                    var ks_breadcrumb_elements  = $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(chart_id_name).nextAll();
                    $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(chart_id_name).addClass('d-none');
                    ks_breadcrumb_elements.each(function(index,item){
                        $(item).addClass("d-none")
                    })
                    $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".ks_chart_heading").removeClass("d-none")
                    $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").find(".ks_list_view_heading").removeClass("d-none")
                    $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").addClass('d-none');
                    $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_chart_info").removeClass('d-none')
                    $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_color_option").removeClass('d-none')
                    $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_quick_edit_action_popup").addClass('d-sm-block ');
                    $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_more_action").removeClass('d-none');
                    $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_action_export").removeClass('d-none')
                    $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_search_plus").removeClass('d-none')
                    $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_search_minus").removeClass('d-none')
                    self.ksFetchChartItem(item_id)
                    var updateValue = self.ks_dashboard_data.ks_set_interval;
                }

            } else {
                if(!domain){
                $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_id + "]").children()[0]).find(".ks_dashboard_item_drill_up").addClass('d-none');
            }

            }
        }

        e.stopPropagation();
    }

     ksFetchChartItem(id) {
        var self = this;
        var item_data = self.ks_dashboard_data.ks_item_data[id];
        const context = self.env.getContext();
        return self._rpc("/web/dataset/call_kw/ks_dashboard_ninja.board/ks_fetch_item",{
            model: 'ks_dashboard_ninja.board',
            method: 'ks_fetch_item',
            args: [
                [item_data.id], self.ks_dashboard_data.ks_dashboard_id, {}
            ],
            kwargs:{ context },
        }).then((new_item_data) => {
            this.ks_dashboard_data.ks_item_data[id] = new_item_data[id];
            this.ks_dashboard_data.ks_item_data[id]['ks_dashboard_item_type'] = new_item_data[id].ks_dashboard_item_type
            this.item.ks_dashboard_item_type = new_item_data[id].ks_dashboard_item_type
            $($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + id + "]").children()[0]).find(".card-body").empty();
            var item_data = self.ks_dashboard_data.ks_item_data[id]
            if (item_data.ks_list_view_data) {
                 self.actionService.doAction({
                    type: "ir.actions.client",
                    tag: "reload",
                 });
            }else if(item_data.ks_dashboard_item_type == 'ks_funnel_chart'){
                $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_data.id + "]").find(".card-body").remove();
                var name = item_data.name ?item_data.name : item_data.ks_model_display_name;
                $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').prop('title',name)
                $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_data.id + "]").find('.ks_chart_heading').text(name)
                ksrenderfunnelchart.bind(this)($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_data.id + "]"),item_data, 'dashboard_view');
            }else{
                $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_data.id + "]").find(".card-body").remove();
                ks_render_graphs.bind(this)($(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + id + "]"), item_data, self.props.dashboard_data.zooming_enabled, 'dashboard_view');
            }
        });
    }



        ksRenderChartColorOptions(e) {
            var self = this;
            if (!$(e.currentTarget).parent().hasClass('global-active')) {
                //            FIXME : Correct this later.
                var $parent = $(e.currentTarget).parent().parent();
                $parent.find('.global-active').removeClass('global-active')
                $(e.currentTarget).parent().addClass('global-active')
                var item_data = self.ks_dashboard_data.ks_item_data[$parent.data().itemId];
                var chart_data = JSON.parse(item_data.ks_chart_data);
                this._rpc("/web/dataset/call_kw/ks_dashboard_ninja.item/write",{
                        model: 'ks_dashboard_ninja.item',
                        method: 'write',
                        args: [$parent.data().itemId, {
                            "ks_chart_item_color": e.currentTarget.dataset.chartColor
                        }],
                        kwargs:{}
                }).then(() => {
                    self.ks_dashboard_data.ks_item_data[$parent.data().itemId]['ks_chart_item_color'] = e.target.dataset.chartColor;
                    $(".grid-stack-item[gs-id=" + item_data.id + "]").find(".card-body").remove();
                    if (item_data.ks_dashboard_item_type == 'ks_funnel_chart'){
                        ksrenderfunnelchart.bind(this)($(self.ks_gridstack_container.el), item_data, 'dashboard_view');
                    }else{
                        ks_render_graphs.bind(this)($(self.ks_gridstack_container.el),item_data, self.props.dashboard_data.zooming_enabled, 'dashboard_view');
                    }
                })
            }
        }

        ksLoadMoreRecords(e) {
            var self = this;
            var ks_intial_count = e.target.parentElement.dataset.prevOffset;
            var ks_offset = e.target.parentElement.dataset.next_offset;
            var itemId = e.currentTarget.dataset.itemId;
            var offset = self.ks_dashboard_data.ks_item_data[itemId].ks_pagination_limit;
            var context = self.ks_dashboard_data['context']
            var params;
            params = self.env.ksGetParamsForItemFetch(parseInt(itemId));
            this._rpc("/web/dataset/call_kw/ks_dashboard_ninja.board/ks_get_list_view_data_offset",{
                model: 'ks_dashboard_ninja.board',
                method: 'ks_get_list_view_data_offset',
                args: [parseInt(itemId), {
                    ks_intial_count: ks_intial_count,
                    offset: ks_offset,
                    }, parseInt(self.ks_dashboard_data.ks_dashboard_id), params],
                kwargs:{context: self.env.getContext()}
            }).then(function(result) {
                var item_data = self.ks_dashboard_data.ks_item_data[itemId];
                if(result.ks_list_view_data){
                    result.ks_list_view_data = convert_data_to_utc(result.ks_list_view_data)
                }
                var item_view = $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_data.id + "]");
                self.item.ks_list_view_data = result.ks_list_view_data;
                self.prepare_list();
                $(e.target).parents('.ks_pager').find('.ks_value').text(result.offset + "-" + result.next_offset);
                e.target.parentElement.dataset.next_offset = result.next_offset;
                e.target.parentElement.dataset.prevOffset = result.offset;
                $(e.target.parentElement).find('.ks_load_previous').removeClass('ks_event_offer_list');
                if (result.next_offset < parseInt(result.offset) + (offset - 1) || result.next_offset == item_data.ks_record_count || result.next_offset === result.limit){
                    $(e.target).addClass('ks_event_offer_list');
                }
            });
        }

        ksLoadPreviousRecords(e) {
            var self = this;
            var itemId = e.currentTarget.dataset.itemId;
            var offset = self.ks_dashboard_data.ks_item_data[itemId].ks_pagination_limit;
            var ks_offset =  parseInt(e.target.parentElement.dataset.prevOffset) - (offset + 1) ;
            var ks_intial_count = e.target.parentElement.dataset.next_offset;
            var context = self.ks_dashboard_data['context']
            var params;
            params = self.env.ksGetParamsForItemFetch(parseInt(itemId));

            this._rpc("/web/dataset/call_kw/ks_dashboard_ninja.board/ks_get_list_view_data_offset",{
                model: 'ks_dashboard_ninja.board',
                method: 'ks_get_list_view_data_offset',
                args: [parseInt(itemId), {
                        ks_intial_count: ks_intial_count,
                        offset: ks_offset,
                    }, parseInt(self.ks_dashboard_data.ks_dashboard_id), params],
                kwargs:{context: self.env.getContext()}
            }).then(function(result) {
                if(result.ks_list_view_data){
                    result.ks_list_view_data = convert_data_to_utc(result.ks_list_view_data)
                }
                var item_data = self.ks_dashboard_data.ks_item_data[itemId];
                var item_view = $(".ks_dashboard_main_content").find(".grid-stack-item[gs-id=" + item_data.id + "]");
                self.item.ks_list_view_data = result.ks_list_view_data;
                self.prepare_list();
                $(e.target).parents('.ks_pager').find('.ks_value').text(result.offset + "-" + result.next_offset);
                e.target.parentElement.dataset.next_offset = result.next_offset;
                e.target.parentElement.dataset.prevOffset = result.offset;
                $(e.target.parentElement).find('.ks_load_next').removeClass('ks_event_offer_list');
                if (result.offset === 1) {
                    $(e.target).addClass('ks_event_offer_list');
                }
            });
        }

        ksOnListItemInfoClick(e) {
            var self = this;
            var item_id = e.currentTarget.dataset.itemId;
            var item_data = self.ks_dashboard_data.ks_item_data[item_id];
            var action = {
                name: _t(item_data.name),
                type: 'ir.actions.act_window',
                res_model: e.currentTarget.dataset.model,
                domain: item_data.ks_domain || [],
                views: [
                    [false, 'list'],
                    [false, 'form']
                ],
                target: 'current',
            }
            if (e.currentTarget.dataset.listViewType === "ungrouped") {
                action['view_mode'] = 'form';
                action['views'] = [
                    [false, 'form']
                ];
                action['res_id'] = parseInt(e.currentTarget.dataset.recordId);
            } else {
                if (e.currentTarget.dataset.listType === "date_type") {
                    var domain = JSON.parse(e.currentTarget.parentElement.parentElement.dataset.domain);
                    action['view_mode'] = 'list';
                    action['context'] = {
                        'group_by': e.currentTarget.dataset.groupby,
                    };
                    action['domain'] = domain;
                } else if (e.currentTarget.dataset.listType === "relational_type") {
                    var domain = JSON.parse(e.currentTarget.parentElement.parentElement.dataset.domain);
                    action['view_mode'] = 'list';
                    action['context'] = {
                        'group_by': e.currentTarget.dataset.groupby,
                    };
                    action['domain'] = domain;
                    action['context']['search_default_' + e.currentTarget.dataset.groupby] = parseInt(e.currentTarget.dataset.recordId);
                } else if (e.currentTarget.dataset.listType === "other") {
                    var domain = JSON.parse(e.currentTarget.parentElement.parentElement.dataset.domain);
                    action['view_mode'] = 'list';
                    action['context'] = {
                        'group_by': e.currentTarget.dataset.groupby,
                    };
                    action['context']['search_default_' + e.currentTarget.dataset.groupby] = parseInt(e.currentTarget.dataset.recordId);
                    action['domain'] = domain;
                }
            }
            self.actionService.doAction(action)
        }

};

Ksdashboardgraph.props = {
    item: { type: Object, optional: true},
    dashboard_data: { type: Object, optional: true},
    ksdatefilter : { type: String ,optional: true},
    pre_defined_filter :{ type:Object, optional: true},
    custom_filter :{ type:Object, optional: true},
    itemsToUpdateList : { type: Array, optional: true },
    ks_speak:{ type: Function , optional: true},
    hideButtons: { type: Number, optional: true },
    generate_dialog: { type: Boolean, optional: true },
    explain_ai_whole: { type: Boolean, optional: true },
    onItemClick: { type: Function },
};

Ksdashboardgraph.template = "Ks_chart_list_container";
Ksdashboardgraph.components = { KsItemButton };
