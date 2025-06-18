/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
const { Component, useEffect, useRef, useState, onMounted } = owl;
import { renderToElement, renderToString } from "@web/core/utils/render";
import { ksrendermapview } from "@ks_dashboard_ninja/js/charts_render_global_functions";


export class KsMapPreview extends Component {
    setup() {
        var self =this;
        this.root =null;
        this.orm = useService("orm");
        this.mapContainerRef = useRef("mapContainer");
        useEffect(() =>{
            if (this.root){
                this.root.dispose()
            }
            this._Ks_render()
        });

    }

    _Ks_render() {
        var self = this;
        var rec = this.props.record.data;
        if ($(self.mapContainerRef.el).find("div.graph_text").length){
            $(self.mapContainerRef.el).find("div.graph_text").remove();
        }
        if (rec.ks_dashboard_item_type === 'ks_map_view'){
            if(rec.ks_data_calculation_type !== "query"){
                if (rec.ks_model_id) {
                    if (rec.ks_chart_groupby_type == 'date_type' && !rec.ks_chart_date_groupby) {
                        return  $(self.mapContainerRef.el).append($("<div class='graph_text'>").text("Select Group by date to create chart based on date groupby"));
                    } else if (rec.ks_chart_data_count_type === "count" && !rec.ks_chart_relation_groupby) {
                        $(self.mapContainerRef.el).append($("<div class='graph_text'>").text("Select Group By to create chart view"));
                    } else if (rec.ks_chart_data_count_type !== "count" && (rec.ks_chart_measure_field.count === 0 || !rec.ks_chart_relation_groupby)) {
                        $(self.mapContainerRef.el).append($("<div class='graph_text'>").text("Select Measure and Group By to create chart view"));
                    } else if (!rec.ks_chart_data_count_type) {
                        $(self.mapContainerRef.el).append($("<div class='graph_text'>").text("Select Chart Data Count Type"));
                    } else {
                        ksrendermapview.bind(this)($(this.mapContainerRef.el), rec, 'preview');
                    }
                } else {
                    $(self.mapContainerRef.el).append($("<div class='graph_text'>").text("Select a Model first."));
                }
            }else if(rec.ks_data_calculation_type === "query" && rec.ks_query_result) {
                if(rec.ks_xlabels && rec.ks_ylabels){
                        ksrendermapview.bind(this)($(this.mapContainerRef.el), rec, 'preview');
                } else {
                    $(self.mapContainerRef.el).append($("<div class='graph_text'>").text("Please choose the X-labels and Y-labels"));
                }
            }else if(rec.ks_data_calculation_type === "query" && this.props.record.data.ks_custom_query) {
                    $(self.mapContainerRef.el).append($("<div class='graph_text'>").text("The query is invalid. Please provide a correctly structured query."));
            }else {
                    $(self.mapContainerRef.el).append($("<div class='graph_text'>").text("Please run the appropriate Query"));
            }
        }

    }

    async _fetchRecordsPartner(data) {
        let domain = [];
        if (data && data['ks_partners_map']) {
            domain = [['id', 'in', JSON.parse(data['ks_partners_map'])]]
        }
        const fields = ["partner_latitude", "partner_longitude", "name"];
        const records = await this.orm.searchRead("res.partner", domain, fields);
        return records
    }

}

KsMapPreview.template = "KsMapPreview";

export const ks_map_preview_field = {
    component:KsMapPreview,
    supportedTypes : ["char"]
};

registry.category("fields").add("ks_dashboard_map_preview", ks_map_preview_field);