/** @odoo-module */

import { registry } from "@web/core/registry";
import { CharField } from "@web/views/fields/char/char_field";
const { Component,reactive, onWillUnmount, onWillUpdateProps, useEffect, useRef, useState, onMounted, willStart } = owl;
import { renderToElement, renderToString } from "@web/core/utils/render";
import { ks_render_graphs } from "@ks_dashboard_ninja/js/charts_render_global_functions";

export class KsGraphPreview extends Component{
    setup(){
    var self =this;
    this.root =null;
    this.graphref = useRef("graph");
    this.kschartref = useRef("kschart");
    useEffect(() => {
        if (this.root){
            this.root.dispose()
        }
        this._Ks_render()
        });

}
      _Ks_render(){
        var self = this;
        var rec = this.props.record.data;
        if ($(self.graphref.el).find("div.graph_text").length){
            $(self.graphref.el).find("div.graph_text").remove();
        }
       if (rec.ks_dashboard_item_type !== 'ks_tile' && rec.ks_dashboard_item_type !== 'ks_kpi' && rec.ks_dashboard_item_type !== 'ks_list_view' && rec.ks_dashboard_item_type !== 'ks_to_do'){
            if(rec.ks_data_calculation_type !== "query"){
                if (rec.ks_model_id) {
                    if (rec.ks_chart_groupby_type == 'date_type' && !rec.ks_chart_date_groupby) {
                        return  $(self.graphref.el).append($("<div class='graph_text'>").text("Select Group by date to create chart based on date groupby"));
                    } else if (rec.ks_dashboard_item_type !== 'ks_scatter_chart' && rec.ks_chart_data_count_type === "count" && !rec.ks_chart_relation_groupby) {
                        $(self.graphref.el).append($("<div class='graph_text'>").text("Select Group By to create chart view"));
                    } else if ( rec.ks_dashboard_item_type !== 'ks_scatter_chart' && rec.ks_chart_data_count_type !== "count" && (rec.ks_chart_measure_field.count === 0 || !rec.ks_chart_relation_groupby)) {
                        $(self.graphref.el).append($("<div class='graph_text'>").text("Select Measure and Group By to create chart view"));
                    } else if (rec.ks_dashboard_item_type !== 'ks_scatter_chart' && !rec.ks_chart_data_count_type) {
                        $(self.graphref.el).append($("<div class='graph_text'>").text("Select Chart Data Count Type"));
                    }else if(rec.ks_dashboard_item_type === "ks_scatter_chart"){
                        if(rec.ks_scatter_measure_x_id && rec.ks_chart_measure_field  ){
                            ks_render_graphs.bind(this)($(this.graphref.el), this.props.record.data, this.props.record.data.zoom_enabled, 'preview');
                        }else{
                            $(self.graphref.el).append($("<div class='graph_text'>").text("Please Choose Measures"));
                        }
                }
                     else {
                        ks_render_graphs.bind(this)($(this.graphref.el), this.props.record.data, this.props.record.data.zoom_enabled, 'preview');
                    }
                } else {
                    $(self.graphref.el).append($("<div class='graph_text'>").text("Select a Model first."));
                }
            }else if(rec.ks_data_calculation_type === "query" && rec.ks_query_result) {
                if(rec.ks_xlabels && rec.ks_ylabels){
                        ks_render_graphs.bind(this)($(this.graphref.el), this.props.record.data, this.props.record.data.zoom_enabled, 'preview');
                } else {
                    $(self.graphref.el).append($("<div class='graph_text'>").text("Please choose the X-labels and Y-labels"));
                }
            }else if(rec.ks_data_calculation_type === "query" && this.props.record.data.ks_custom_query) {
                    $(self.graphref.el).append($("<div class='graph_text'>").text("The query is invalid. Please provide a correctly structured query."));
            }else {
                    $(self.graphref.el).append($("<div class='graph_text'>").text("Please run the appropriate Query"));
            }

        }
    }

}
KsGraphPreview.template = "Ksgraphview";
export const KsGraphPreviewfield = {
    component:KsGraphPreview,
    supportedTypes : ["char"]
};
registry.category("fields").add("ks_dashboard_graph_preview", KsGraphPreviewfield);