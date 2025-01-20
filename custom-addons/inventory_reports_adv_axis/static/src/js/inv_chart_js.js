odoo.define('inv_reports_sharing_for_graph.MyCustomAction1',  function (require) {
"use strict";
//import { deserializeDateTime } from "@web/core/l10n/dates";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var rpc = require('web.rpc');
//var ActionManager = require('web.ActionManager');
var view_registry = require('web.view_registry');
var Widget = require('web.Widget');
var ajax = require('web.ajax');
var session = require('web.session');
var web_client = require('web.web_client');
var _t = core._t;
var QWeb = core.qweb;


var MyCustomAction1 = AbstractAction.extend({
    template: 'ProductDashboardView',
    cssLibs: [
    ],
    jsLibs: [
        'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.9.4/Chart.js'

    ],



    init: function(parent, context) {
    console.log("init----------------")
        this._super(parent, context);
        var employee_data = [];
        var self = this;
    },

    start: function() {
    console.log("Starts--------------------")
        var self = this;

//        self.render_dashboards();
//        self.render_graphs();
        self.graph_product_data();
        self.graph_recent_prod();
//        self.graph_product_turnover();

        return this._super();

    },

    reload: function () {
            window.location.href = this.href;
    },
    getRandomColor: function () {
    console.log("getRandomColor--------------------------")
        var letters = '0123456789ABCDEF'.split('');
        var color = '#';
        for (var i = 0; i < 6; i++ ) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    },


    graph_recent_prod: function() {
        var self = this
        var color = this.$el.find('#color_filter3').val();
        if (color == 'cool'){
            $('.price_product').addClass('cool_color');
        }
        else {
            $('.price_product').addClass('warm_color');
        }
        var ctx = this.$el.find('#sale_order_generated')
        Chart.plugins.register({
          beforeDraw: function(chartInstance) {
            var ctx = chartInstance.chart.ctx;
            ctx.fillStyle = "white";
            ctx.fillRect(0, 0, chartInstance.chart.width, chartInstance.chart.height);
          }
        });
        var bg_color_list = []
        for (var i=0;i<=12;i++){
            bg_color_list.push(self.getRandomColor())
        }
        rpc.query({
                model: 'inventory.valuation',
                method: 'get_product_data_dict',


            })
            .then(function (result) {
                var myChart = new Chart(ctx, {
                type: 'line',
                data: {

                    labels: result.payroll_label,
                    datasets: [{
                        label: 'Product Qty',
                        data: result.payroll_dataset,
                        backgroundColor: bg_color_list,
                        borderColor: bg_color_list,
                        borderWidth: 1,
                        pointBorderColor: 'white',
                        pointBackgroundColor: 'black',
                        pointRadius: 5,
                        pointHoverRadius: 10,
                        pointHitRadius: 30,
                        pointBorderWidth: 2,
                        pointStyle: 'rectRounded'
                    }]
                },
                options: {
                    scales: {
                        yAxes: [{
                            ticks: {
                                min: 0,
                                max: Math.max.apply(null,result.payroll_dataset),
                                //min: 1000,
                                //max: 100000,
                                stepSize: result.
                                payroll_dataset.reduce((pv,cv)=>{return pv + (parseFloat(cv)||0)},0)
                                /result.payroll_dataset.length
                              }
                        }]
                    },
                    responsive: true,
                    maintainAspectRatio: true,
                    legend: {
                        display: true,
                        labels: {
                            fontColor: 'light blue'
                        }
                },
            },
        });

            });


    },

     graph_product_data: function() {
     console.log("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
     debugger;
     if (this.searchModelConfig.context.active_model == 'inventory.valuation')
     {
           var self = this;
        var color = this.$el.find('#color_filter1').val();
        if (color == 'cool'){
            $('.high_price').addClass('cool_color');
        }
        else {
            $('.high_price').addClass('warm_color');
        }

        var option = this.$el.find('#sales_filter').val();
        var ctx = this.$el.find('#highprice')
        Chart.plugins.register({
          beforeDraw: function(chartInstance) {
            var ctx = chartInstance.chart.ctx;
            ctx.fillStyle = "white";
            ctx.fillRect(0, 0, chartInstance.chart.width, chartInstance.chart.height);
          }
        });
        var bg_color_list = []
        for (var i=0;i<=12;i++){
            bg_color_list.push(self.getRandomColor())
        }
        rpc.query({
                model: 'inventory.valuation',
                method: 'get_product_data_dict',
                args:[],
            })
            .then(function (result) {
                var get_data=[];
                for (var i = 0;i < result.payroll_label.length; i++) {
                    var dict = {};
                    var key  = result.payroll_label[i];
                    var val = result.payroll_dataset[i];
                    dict['Customer'] =  key;
                    dict['Total'] =  val;
                    get_data[i] = dict;
                }
                var chart = new Chart(ctx, {
                type: 'bar',
                data: {

                    labels: result.payroll_label,
                    datasets: [{
                        label: 'Quantity',
                        data: result.payroll_dataset,
                        backgroundColor: bg_color_list,
                        borderColor: bg_color_list,
                        borderWidth: 1,
                        pointBorderColor: 'white',
                        pointBackgroundColor: 'red',
                        pointRadius: 5,
                        pointHoverRadius: 10,
                        pointHitRadius: 30,
                        pointBorderWidth: 2,
                        pointStyle: 'rectRounded'
                    }],
                    dataPoints: get_data,
                },
                options: {
                    scales: {
                        yAxes: [{
                            ticks: {
                                min: 0,
                                max: Math.max.apply(null,result.payroll_dataset),
                                //min: 1000,
                                //max: 100000,
                                stepSize: result.
                                payroll_dataset.reduce((pv,cv)=>{return pv + (parseFloat(cv)||0)},0)
                                /result.payroll_dataset.length,
                                                    userCallback: function(value, index, values) {
                                    // Convert the number to a string and splite the string every 3 charaters from the end
                                    value = value.toString();
                                    value = value.split(/(?=(?:...)*$)/);
                                    // Convert the array to a string and format the output
                                    value = value.join(',');
                                    return value;
                                   }
                            }
                        }]
                    },
                    responsive: true,
                    maintainAspectRatio: true,
                    legend: {
                        display: true,
                        labels: {
                            fontColor: 'black'
                        }
                },
            },
        });
        var csv_file = self.$el.find('#downloadCSV');
        csv_file.click(function(){
            self.exportcsv({ filename: "chart-data.csv", chart: chart })
        });

        });
    }



     }





});
core.action_registry.add("inventory_valuation", MyCustomAction1);
return MyCustomAction1
});
