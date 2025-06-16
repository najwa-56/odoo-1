/** @odoo-module **/

import { Component, useState, useEffect, onMounted } from "@odoo/owl"
import { useForwardRefToParent } from "@web/core/utils/hooks";
import { Ksdashboardtile } from '../ks_dashboard_tile_view/ks_dashboard_tile';
import { Ksdashboardtodo } from '../ks_dashboard_to_do_item/ks_dashboard_to_do';
import { Ksdashboardkpiview } from '../ks_dashboard_kpi_view/ks_dashboard_kpi';
import { Ksdashboardgraph } from '../ks_dashboard_graphs/ks_dashboard_graphs';
import { isMobileOS } from "@web/core/browser/feature_detection";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";


export class KsItems extends Component {
    static props = {
        ks_data : { type: Object, optional:true },
        domain_data_obj : { type: Object, optional:true },
        itemsToUpdateList : { type: Array, optional:true },
        date_filter_data : { type: String, optional:true },
        gridStackRootRef: { type: Function, optional: true },
    }
    static template = "Ks_items"
    static components = { Ksdashboardtile, Ksdashboardtodo, Ksdashboardkpiview, Ksdashboardgraph }

    setup(){
        this.ks_dashboard_data = this.props.ks_data
        this.on_dialog = false;
        this.gridstackConfig = {};
        this.actionService = useService('action');
        this.gridStackRootRef = useForwardRefToParent("gridStackRootRef")
        this.explain_ai_whole = true;
        this.gridstack_options = {
            staticGrid:true,
            float: false,
            cellHeight: 68,
            styleInHead : true,
            disableOneColumnMode: true,
        };
        if (isMobileOS()) {
            this.gridstack_options.disableOneColumnMode = false
        }
        onMounted( () => this.onMount())

    }

    onMount(){
        this.grid = GridStack.init(this.gridstack_options, $(".grid-stack")[0]);
        if(!this.env.inDialog)   this.grid_initiate();
    }

    grid_initiate(){
        var self=this;
        var $gridstackContainer = $(".grid-stack");
        if($gridstackContainer.length){
            var item = self.ksSortItems(self.ks_dashboard_data.ks_item_data)
            if(this.ks_dashboard_data.ks_gridstack_config){
                this.gridstackConfig = JSON.parse(this.ks_dashboard_data.ks_gridstack_config);
            }
            for (var i = 0; i < item.length; i++) {
                var graphs = ['ks_scatter_chart','ks_bar_chart', 'ks_horizontalBar_chart', 'ks_line_chart', 'ks_area_chart', 'ks_doughnut_chart','ks_polarArea_chart','ks_pie_chart','ks_flower_view', 'ks_radar_view','ks_radialBar_chart','ks_map_view','ks_funnel_chart','ks_bullet_chart', 'ks_to_do', 'ks_list_view']
                var $ks_preview = $('#' + item[i].id)
                if ($ks_preview.length && !this.ks_dashboard_data.ks_ai_explain_dash) {
                    if (item[i].id in self.gridstackConfig) {
                        var min_width = graphs.includes(item[i].ks_dashboard_item_type) ? 3 : 2
                         self.grid.addWidget($ks_preview[0], {x:self.gridstackConfig[item[i].id].x, y:self.gridstackConfig[item[i].id].y, w:self.gridstackConfig[item[i].id].w, h: self.gridstackConfig[item[i].id].h, autoPosition:isMobileOS, minW:min_width, maxW:null, minH:3, maxH:null, id:item[i].id});
                    } else if ( graphs.includes(item[i].ks_dashboard_item_type)) {
                         self.grid.addWidget($ks_preview[0], {x:0, y:0, w:5, h:6,autoPosition:isMobileOS,minW:4,maxW:null,minH:3,maxH:null, id :item[i].id});
                    }else{
                        self.grid.addWidget($ks_preview[0], {x:0, y:0, w:2, h:2,autoPosition:isMobileOS,minW:2,maxW:null,minH:3,maxH:2,id:item[i].id});
                    }
                }else{
                    if (item[i].id in self.gridstackConfig) {
                        var min_width = graphs.includes(item[i].ks_dashboard_item_type)? 3:2
                         self.grid.addWidget($ks_preview[0], {x:self.gridstackConfig[item[i].id].x, y:self.gridstackConfig[item[i].id].y, w:12, h: 6, autoPosition:isMobileOS, minW:min_width, maxW:null, minH:2, maxH:null, id:item[i].id});
                    } else  {
                         self.grid.addWidget($ks_preview[0], {x:0, y:0, w:12, h:6,autoPosition:isMobileOS,minW:4,maxW:null,minH:3,maxH:null, id :item[i].id});
                    }

                }
            }
            this.grid.setStatic(true);
        }

    }

    ksSortItems(ks_item_data) {
        let items = []
        let self = this;
        var item_data = Object.assign({}, ks_item_data);
        if (self.ks_dashboard_data.ks_gridstack_config) {
            self.gridstackConfig = JSON.parse(self.ks_dashboard_data.ks_gridstack_config);
            let a = Object.values(self.gridstackConfig);
            let b = Object.keys(self.gridstackConfig);
            for (var i = 0; i < a.length; i++) {
                a[i]['id'] = b[i];
            }
            a.sort(function(a, b) {
                return (35 * a.y + a.x) - (35 * b.y + b.x);
            });
            for (let i = 0; i < a.length; i++) {
                if (item_data[a[i]['id']]) {
                    items.push(item_data[a[i]['id']]);
                    delete item_data[a[i]['id']];
                }
            }
        }

        return items.concat(Object.values(item_data));
    }

    _onKsItemClick(item_id){
        let self = this;
        let action ;
            if(self.env.mode === 'edit' || this.env.inDialog)   return;
                let item_data = self.ks_dashboard_data.ks_item_data[item_id];
                if (item_data && item_data.ks_show_records && item_data.ks_data_calculation_type != 'query' && item_data.ks_model_name) {

                    if (item_data.action) {
                        action = Object.assign({}, item_data.action);
                        if (action.view_mode.includes('tree')) action.view_mode = action.view_mode.replace('tree', 'list');
                        for (var i = 0; i < action.views.length; i++) action.views[i][1].includes('tree') ? action.views[i][1] = action.views[i][1].replace('tree', 'list') : action.views[i][1];
                        action['domain'] = item_data.ks_domain || [];
                        action['search_view_id'] = [action.search_view_id, 'search']

                    } else {
                         action = {
                            name: _t(item_data.name),
                            type: 'ir.actions.act_window',
                            res_model: item_data.ks_model_name,
                            domain: item_data.ks_domain || "[]",
                            views: [
                                [false, 'list'],
                                [false, 'form']
                            ],
                            view_mode: 'list',
                            target: 'current',
                        }
                    }

                    if(action){
                        self.actionService.doAction(action);
                    }
                }
    }

    async speak_once(ev,item){
        ev.preventDefault()
        var ks_audio = ev.currentTarget;
        let ks_speeches = []
        ev.currentTarget.parentElement.querySelector('.voice-cricle').classList.toggle("d-none");
        ev.currentTarget.parentElement.querySelector('.comp-gif').classList.toggle("d-none");
        $(document.querySelectorAll('audio')).each((index,item)=>{
            if ($(ks_audio).find('audio')[0] !== item && !item.paused){
                item.pause()
                item.parentElement?.querySelector('.voice-cricle')?.classList.toggle("d-none");
                item.parentElement?.querySelector('.comp-gif')?.classList.toggle("d-none");
            }
        })
        if (!ks_speeches.length){
            if ($(ks_audio).find('audio').attr('src') && $(ks_audio).find('audio')[0].paused){
                $(ks_audio).find('audio')[0].play();
                $(ks_audio).find('.fa.fa-volume-up').removeClass('d-none');
                $(ks_audio).find('.comp-gif').removeClass('d-none');
                $(ks_audio).find('.voice-cricle').addClass('d-none');
                $(ks_audio).find('.fa.fa-pause').remove();
            }else if ($(ks_audio).find('audio').attr('src') && !$(ks_audio).find('audio')[0].paused){
                $(ks_audio).find('audio')[0].pause();
                $(ks_audio).find('.voice-cricle').removeClass('d-none');
                $(ks_audio).find('.comp-gif').addClass('d-none');
                $(ks_audio).find('.fa.fa-volume-up').addClass('d-none');
            }else{
                $(ks_audio).find('.comp-gif').removeClass('d-none');
                $(ks_audio).find('.voice-cricle').addClass('d-none');
                ks_speeches.push(this.env.services.rpc('web/dataset/call_kw/ks_dashboard_ninja.arti_int/ks_generatetext_to_speech',{
                    model : "ks_dashboard_ninja.arti_int",
                    method:"ks_generatetext_to_speech",
                    args:[item.id],
                    kwargs:{}
                    }).then(function(result){
                        if (result){
                            $(ks_audio).find('span').removeClass('d-none')
                            var audio = (JSON.parse(result)).snd;
                            $(ks_audio).find('audio')[0].src="data:audio/wav;base64, "+audio;
                            $(ks_audio).find('audio')[0].play()
                            ks_speeches.pop()
                        }
                        else{
                            $(ks_audio).find('.comp-gif').addClass('d-none');
                            $(ks_audio).find('.voice-cricle').removeClass('d-none');
                            ks_speeches.pop()
                        }
                    }.bind(this))
                )
                return Promise.resolve(ks_speeches)
            }
        }
    }

}

