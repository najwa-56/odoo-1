/** @odoo-module **/

import { renderToString } from "@web/core/utils/render";
import { localization } from "@web/core/l10n/localization";


export function ks_render_graphs($ks_gridstack_container, item, zooming_enabled, view){
    try {
        const isRtl = localization.direction === "rtl"
        var self =this;
        let graph_render;
        if(view === 'dashboard_view'){
            if($ks_gridstack_container.find('.ks_chart_card_body').length){
                graph_render = $ks_gridstack_container.find('.ks_chart_card_body')[0];
            }else{
                $($ks_gridstack_container.find('.ks_dashboarditem_chart_container')[0]).append("<div class='card-body ks_chart_card_body'>");
                graph_render = $ks_gridstack_container.find('.ks_chart_card_body')[0];
            }
        }
        else if(view === 'preview'){
            if($ks_gridstack_container.find(".graph_text").length){
                $ks_gridstack_container.find(".graph_text").remove();
            }
            graph_render = $ks_gridstack_container[0]
        }
        const chart_data = JSON.parse(item.ks_chart_data);
        var ks_labels = chart_data['labels'];
        var ks_data = chart_data.datasets;

        if(item.ks_chart_cumulative_field && ks_data?.length){
        for(var i=0;i<ks_data.length;i++){
            var ks_temp_com = 0;
            var datasets = {};
            var cumulative_data = []
            if(ks_data[i].ks_chart_cumulative_field){
                for(var j=0; j< ks_data[i].data.length; j++){
                    ks_temp_com = ks_temp_com + ks_data[i].data[j];
                    cumulative_data.push(ks_temp_com);
                }
                datasets.label = 'Cumulative ' + ks_data[i].label;
                datasets.data = cumulative_data;
                if(item.ks_chart_cumulative){
                    datasets.type = 'line';
                }
                ks_data.push(datasets);
            }
        }
    }


        let data=[];
        if (ks_data && ks_labels){
        if (ks_data.length && ks_labels.length){
            for (let i=0 ; i<ks_labels.length ; i++){
                let data2={};
                for (let j=0 ;j<ks_data.length ; j++){
                    if (ks_data[j].type == "line"){
                    data2[ks_data[j].label] = ks_data[j].data[i]
                    }else{
                    data2[ks_data[j].label] = ks_data[j].data[i]
                    }
                }
                data2["category"] = ks_labels[i]
                data.push(data2)
            }

            const root  = am5.Root.new(graph_render);
            this.root = root;

            const theme = item.ks_chart_item_color
        switch(theme){
            case "default":
                root.setThemes([am5themes_Animated.new(root)]);
                break;
            case "dark":
                root.setThemes([am5themes_Dataviz.new(root)]);
                break;
            case "material":
                root.setThemes([am5themes_Material.new(root)]);
                break;
            case "moonrise":
                root.setThemes([am5themes_Moonrise.new(root)]);
                break;
        };
        var chart_type = item.ks_dashboard_item_type
        switch (chart_type){
            case "ks_bar_chart":
            case "ks_bullet_chart":
                if(zooming_enabled){
                    var wheely_val = "zoomX";
                }else{
                    var wheely_val = 'none';
                }
            var chart = root.container.children.push(am5xy.XYChart.new(root, {panX: false,panY: false,
             wheelX: "panX",wheelY: wheely_val,layout: root.verticalLayout}));
//            chart.set("autoFit", true);
//            root.rtl = true
            var xRenderer = am5xy.AxisRendererX.new(root, {
                   minGridDistance: 15,
                   minorGridEnabled: true
            });

            if (chart_type=='ks_bar_chart'){
                var rotations_angle = -45
            }
            else{
                rotations_angle = -90
            }

            xRenderer.labels.template.setAll({
              direction: "rtl",
              rotation: rotations_angle,
              centerY: am5.p50,
              centerX: am5.p100,
              paddingRight: 10
            });

            var xAxis = chart.xAxes.push(am5xy.CategoryAxis.new(root, {categoryField: "category",
            renderer: xRenderer,tooltip: am5.Tooltip.new(root, {})}));

            xRenderer.grid.template.setAll({location: 1})

            xAxis.data.setAll(data);

            var yAxis = chart.yAxes.push(am5xy.ValueAxis.new(root, {extraMin: 0,
            extraMax: 0.1,renderer: am5xy.AxisRendererY.new(root, {strokeOpacity: 0.1}) }));

            let label_format_text = item.ks_data_format === "exact" ? "{valueY.formatNumber('0.00')}" : "{valueY}"

            if(isRtl){
                yAxis.get("renderer").labels.template.setAll({
                    paddingRight: 30,
                     paddingLeft: 30
                });
            }
            // Add series

            for (let k = 0;k<ks_data.length ; k++){
                if (item.ks_dashboard_item_type == "ks_bar_chart" && item.ks_bar_chart_stacked == true && ks_data[k].type != "line"){
                    var tooltip = am5.Tooltip.new(root, {
                        pointerOrientation: "horizontal",
                        textAlign: "center",
                        centerX: am5.percent(96),
                        labelText: `{categoryX}, {name}: ${label_format_text}`
                    });
                    tooltip.label.setAll({
                        direction: "rtl"
                    })

                    var series = chart.series.push(am5xy.ColumnSeries.new(root, {
                        stacked: true,
                        name: `${ks_data[k].label}`,
                        xAxis: xAxis,
                        yAxis: yAxis,
                        valueYField:`${ks_data[k].label}`,
                        categoryXField: "category",
                        tooltip: tooltip
                    }));
                    series.columns.template.events.on("click",function(ev){
                        if (item.ks_data_calculation_type === 'custom' && self.ks_dashboard_data && !self.ks_dashboard_data['ks_ai_dashboard']){
                            self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                        }
                    });
                    series.data.setAll(data);
                }
                else if (item.ks_dashboard_item_type == "ks_bar_chart" && ks_data[k].type != "line"){
                    var tooltip = am5.Tooltip.new(root, {
                        textAlign: "center",
                        centerX: am5.percent(96),
                        pointerOrientation: "horizontal",
                        labelText: "{categoryX}, {name}: {valueY}"
                    });
                    tooltip.label.setAll({
                        direction: "rtl"
                    })

                    var series = chart.series.push(am5xy.ColumnSeries.new(root, {
                        name: `${ks_data[k].label}`,
                        xAxis: xAxis,
                        yAxis: yAxis,
                        valueYField:`${ks_data[k].label}`,
                        categoryXField: "category",
                        tooltip: tooltip

                    }));
                    series.columns.template.events.on("click",function(ev){
                        if (item.ks_data_calculation_type === 'custom' && self.ks_dashboard_data && !self.ks_dashboard_data['ks_ai_dashboard']){
                            self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                        }
                    });
                    series.data.setAll(data);

                }
                else if (item.ks_dashboard_item_type == "ks_bullet_chart"){
                    var tooltip = am5.Tooltip.new(root, {
                        textAlign: "center",
                        centerX: am5.percent(96),
                        labelText: `${ks_data[k].label}: {valueY}`
                    });
                    tooltip.label.setAll({
                        direction: "rtl"
                    })

                    var series = chart.series.push(am5xy.ColumnSeries.new(root, {
                    name: `${ks_data[k].label}`,
                    xAxis: xAxis,
                    yAxis: yAxis,
                    valueYField:`${ks_data[k].label}`,
                    categoryXField: "category",
                    clustered: false,
                    tooltip: tooltip,
                     ...(isRtl && { direction: "rtl" }),
                    }));

                    series.columns.template.setAll({
                        width: am5.percent(80-(10*k)),
                        tooltipY: 0,
                        strokeOpacity: 0
                    });
                    series.columns.template.events.on("click",function(ev){
                        if (item.ks_data_calculation_type === 'custom' && self.ks_dashboard_data && !self.ks_dashboard_data['ks_ai_dashboard']){
                            self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                        }
                    });
                    series.data.setAll(data);
                }

                if (item.ks_show_records == true && series){
                    series.columns.template.setAll({
                        tooltipY: 0,
                        templateField: "columnSettings"
                   });
                    var cursor = chart.set("cursor", am5xy.XYCursor.new(root, {
                            behavior: "zoomY"
                    }));
                   cursor.lineY.set("forceHidden", true);
                   cursor.lineX.set("forceHidden", true);
                }
                if (item.ks_show_data_value == true && series){
                    series.bullets.push(function () {
                        return am5.Bullet.new(root, {
//                            locationY:1,
                                sprite: am5.Label.new(root, {
                                  text:  label_format_text,
                                  centerY: am5.p100,
                                  centerX: am5.p50,
                                  populateText: true,
                                  ...(isRtl && {direction: "rtl"}),
                                })
                        });
                    });
                }
                if (item.ks_dashboard_item_type == "ks_bar_chart" && item.ks_chart_measure_field_2 && ks_data[k].type == "line"){
                    var tooltip = am5.Tooltip.new(root, {
                        textAlign: "center",
                        centerX: am5.percent(96),
                        pointerOrientation: "horizontal",
                        labelText: "{categoryX}, {name}: {valueY}"
                    });
                    tooltip.label.setAll({
                        direction: "rtl"
                    })

                    var series2 = chart.series.push(
                        am5xy.LineSeries.new(root, {
                            name: `${ks_data[k].label}`,
                            xAxis: xAxis,
                            yAxis: yAxis,
                            valueYField:`${ks_data[k].label}`,
                            categoryXField: "category",
                            tooltip: tooltip
                        })
                    );

                    series2.strokes.template.setAll({strokeWidth: 3,templateField: "strokeSettings"});
                    series2.strokes.template.events.on("click",function(ev){
                        if (item.ks_data_calculation_type === 'custom' && self.ks_dashboard_data && !self.ks_dashboard_data['ks_ai_dashboard']){
                            self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                        }
                    });
                    series2.data.setAll(data);

                    series2.bullets.push(function() {
                        return am5.Bullet.new(root, {
                            sprite: am5.Circle.new(root, {
                                strokeWidth: 3,
                                stroke: series2.get("stroke"),
                                radius: 5,
                                fill: root.interfaceColors.get("background")
                            })
                        });
                    });
                }
            }
            break;
            case "ks_horizontalBar_chart":
                if(zooming_enabled){
                    var wheely_val = "zoomX";
                }else{
                    var wheely_val = 'none';
                }
                var chart = root.container.children.push(am5xy.XYChart.new(root, {panX: false,panY: false,
                wheelX: "panX",wheelY: wheely_val,layout: root.verticalLayout}));
                var yRenderer = am5xy.AxisRendererY.new(root, {
                        inversed: true,
                        minGridDistance: 30,
                        minorGridEnabled: true,
                        cellStartLocation: 0.1,
                        cellEndLocation: 0.9
                    })
                yRenderer.labels.template.setAll({
                      direction: "rtl",
                });
                var yAxis = chart.yAxes.push(am5xy.CategoryAxis.new(root, {
                    categoryField: "category",
                    renderer: yRenderer
                }))

                yAxis.data.setAll(data);

                var xAxis = chart.xAxes.push(am5xy.ValueAxis.new(root, {
                    renderer: am5xy.AxisRendererX.new(root, {
                        strokeOpacity: 0.1
                    }),
                    min: 0
                }));
                for (let k = 0;k<ks_data.length ; k++){
                    var tooltip = am5.Tooltip.new(root, {
                        textAlign: "center",
                        centerX: am5.percent(96),
                        pointerOrientation: "horizontal",
                        labelText: "{categoryY}, {name}: {valueX}"
                    });

                    tooltip.label.setAll({
                        direction: "rtl"
                    })

                if (item.ks_bar_chart_stacked == true){
                    var series = chart.series.push(am5xy.ColumnSeries.new(root, {
                        stacked: true,
                        name: `${ks_data[k].label}`,
                        xAxis: xAxis,
                        yAxis: yAxis,
                        valueXField:`${ks_data[k].label}`,
                        categoryYField: "category",
                        sequencedInterpolation: true,
                        tooltip: tooltip
                    }));

                }else if (item.ks_dashboard_item_type == "ks_horizontalBar_chart" && ks_data[k].type != "line"){
                    var series = chart.series.push(am5xy.ColumnSeries.new(root, {
                        name: `${ks_data[k].label}`,
                        xAxis: xAxis,
                        yAxis: yAxis,
                        valueXField:`${ks_data[k].label}`,
                        categoryYField: "category",
                        sequencedInterpolation: true,
                        tooltip: tooltip

                    }));
                }
                    if (item.ks_show_records == true && series){
                        series.columns.template.setAll({
    //                        width: am5.percent(80-(10*k)),
                            height: am5.p100,
                            strokeOpacity: 0
                       });
                       var cursor = chart.set("cursor", am5xy.XYCursor.new(root, {
                                behavior: "zoomY"
                        }));
                       cursor.lineY.set("forceHidden", true);
                       cursor.lineX.set("forceHidden", true);
                    }
                    if (item.ks_show_data_value == true && series){
                        let label_format_text = item.ks_data_format === "exact" ? "{valueX.formatNumber('0.00')}" : "{valueX}"
                        series.bullets.push(function () {
                            return am5.Bullet.new(root, {
    //                            locationX: 1,
                                    sprite: am5.Label.new(root, {
                                      text:  label_format_text,
                                      centerY: am5.p50,
                                      centerX: am5.p50,
                                      populateText: true,
                                      ...(isRtl && {direction: "rtl"})
                                    })
                            });
                        });
                    }
                    if (series){
                        series.columns.template.events.on("click",function(ev){
                            if (item.ks_data_calculation_type === 'custom' && self.ks_dashboard_data && !self.ks_dashboard_data['ks_ai_dashboard']){
                                self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                            }
                        });

                        series.data.setAll(data);
                    }

                 if (item.ks_dashboard_item_type == "ks_horizontalBar_chart" && ks_data[k].type == "line"){
                    var series2 = chart.series.push(
                        am5xy.LineSeries.new(root, {
                            name: `${ks_data[k].label}`,
                            xAxis: xAxis,
                            yAxis: yAxis,
                            valueXField:`${ks_data[k].label}`,
                            categoryYField: "category",
                            sequencedInterpolation: true,
                            tooltip: am5.Tooltip.new(root, {
                                pointerOrientation: "horizontal",
                                labelText: "{categoryY}, {name}: {valueX}"
                            })
                        })
                    );

                    series2.strokes.template.setAll({strokeWidth: 3,templateField: "strokeSettings"});
                    series2.strokes.template.events.on("click",function(ev){
                        if (item.ks_data_calculation_type === 'custom' && self.ks_dashboard_data && !self.ks_dashboard_data['ks_ai_dashboard']){
                            self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                        }
                    });


                    series2.bullets.push(function() {
                        return am5.Bullet.new(root, {
                            sprite: am5.Circle.new(root, {
                                strokeWidth: 3,
                                stroke: series2.get("stroke"),
                                radius: 5,
                                fill: root.interfaceColors.get("background")
                            })
                        });
                    });
                     series2.data.setAll(data);
                }
            }
            break;
            case "ks_line_chart":
            case "ks_area_chart":
                if(zooming_enabled){
                    var wheely_val = "zoomX";
                }else{
                    var wheely_val = 'none';
                }

                var chart = root.container.children.push(am5xy.XYChart.new(root, {panX: false,panY: false,
                wheelX: "panX",wheelY: wheely_val,layout: root.verticalLayout}));
                var xRenderer = am5xy.AxisRendererX.new(root, {
                    minGridDistance: 15,
                    minorGridEnabled: true
                    });
                xRenderer.labels.template.setAll({
                      direction: "rtl",
                  rotation: -45,
                  centerY: am5.p50,
                  centerX: am5.p100,
                  paddingRight: 10
                });
                var xAxis = chart.xAxes.push(am5xy.CategoryAxis.new(root, {
                    categoryField: "category",
                    maxDeviation: 0.2,
                    renderer: xRenderer,
                    tooltip: am5.Tooltip.new(root, {})
                }));
                xAxis.data.setAll(data);

                var yAxis = chart.yAxes.push(am5xy.ValueAxis.new(root, {extraMin: 0,
                extraMax: 0.1,renderer: am5xy.AxisRendererY.new(root, {strokeOpacity: 0.1}) }));

                 if(isRtl){
                    yAxis.get("renderer").labels.template.setAll({
                        paddingRight: 30,
                        paddingLeft: 30
                    });
                 }

                for (let k = 0;k<ks_data.length ; k++){

                    var tooltip = am5.Tooltip.new(root, {
                        textAlign: "center",
                        centerX: am5.percent(96),
                        labelText: "[bold]{categoryX}[/]\n{name}: {valueY}"
                    });
                    tooltip.label.setAll({
                        direction: "rtl"
                    })

                    var series = chart.series.push(am5xy.LineSeries.new(root, {
                        name: `${ks_data[k].label}`,
                        xAxis: xAxis,
                        yAxis: yAxis,
                        valueYField: `${ks_data[k].label}`,
                        categoryXField: "category",
                        alignLabels: true,
                        tooltip: tooltip
                    }));
                    series.strokes.template.setAll({strokeWidth: 2,templateField: "strokeSettings"});

                    series.bullets.push(function() {
                        var graphics = am5.Rectangle.new(root, {
                            width:7,
                            height:7,
                            centerX:am5.p50,
                            centerY:am5.p50,
                            fill: series.get("stroke")
                        });
                        if (item.ks_dashboard_item_type == "ks_area_chart" || item.ks_dashboard_item_type == "ks_line_chart"){
                            graphics.events.on("click", function(ev) {
                                if (item.ks_data_calculation_type === 'custom' && self.ks_dashboard_data && !self.ks_dashboard_data['ks_ai_dashboard']){
                                    self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                                }
                            });
                        }
                        return am5.Bullet.new(root, {
                            sprite: graphics
                        });
                    });
                    if (item.ks_show_data_value == true && series){
                        let label_format_text = item.ks_data_format === "exact" ? "{valueY.formatNumber('0.00')}" : "{valueY}"
                        series.bullets.push(function () {
                            return am5.Bullet.new(root, {
                                sprite: am5.Label.new(root, {
                                    text:  label_format_text,
                                    centerX:am5.p50,
                                    centerY:am5.p100,
                                    populateText: true,
                                    ...(isRtl && {direction: "rtl"})
                                 })
                            });
                        });
                    }
                    if (item.ks_dashboard_item_type === "ks_area_chart"){
                        series.fills.template.setAll({
                            fillOpacity: 0.5,
                            visible: true
                        });
                    }

                    series.data.setAll(data);
                }

                if (item.ks_show_records == true){
                    var cursor = chart.set("cursor", am5xy.XYCursor.new(root, {
                        behavior: "none"
                    }));
                    cursor.lineY.set("forceHidden", true);
                    cursor.lineX.set("forceHidden", true);

                }
                break;
                case "ks_pie_chart":
                case "ks_doughnut_chart":
                    var series = []
                    if (item.ks_semi_circle_chart == true && (item.ks_dashboard_item_type == "ks_pie_chart" ||item.ks_dashboard_item_type == "ks_doughnut_chart")){
                         if (item.ks_dashboard_item_type == 'ks_doughnut_chart'){
                            var chart = root.container.children.push(
                                am5percent.PieChart.new(root, {
                                   innerRadius : am5.percent(50),
                                   layout: root.verticalLayout,
                                   startAngle: 180,
                                   endAngle: 360,
                            }));
                        }else{
                            var chart = root.container.children.push(
                                am5percent.PieChart.new(root, {
                                    radius: am5.percent(90),
                                    layout: root.verticalLayout,
                                    startAngle: 180,
                                    endAngle: 360,
                                }));
                        }
                        var legend = chart.children.push(am5.Legend.new(root, {
                          centerX: am5.percent(50),
                          x: am5.percent(50),
                          layout: am5.GridLayout.new(root, {
                            maxColumns: 3,
                            fixedWidthGrid: true
                          }),
                          y: am5.percent(100),
                          centerY: am5.percent(100),
                          reverseChildren: true,
                        }));
                        if(isRtl){
                           legend.labels.template.setAll({
                               textAlign: "right"
                           });
                           legend.itemContainers.template.setAll({
                                reverseChildren: true,
                                paddingLeft: 20,
                                paddingRight: 20,
                           });
                       }
                        for (let k = 0;k<ks_data.length ; k++){
                            series[k] = chart.series.push(
                                am5percent.PieSeries.new(root, {
                                name: `${ks_data[k].label}`,
                                valueField: `${ks_data[k].label}`,
                                categoryField: "category",
                                alignLabels: false,
                                startAngle: 180,
                                endAngle: 360,
                            }));
                        }
                    }else{
                        if (item.ks_dashboard_item_type == "ks_doughnut_chart"){
                            var chart = root.container.children.push(
                                am5percent.PieChart.new(root, {
                                innerRadius: am5.percent(50),
                                layout: root.verticalLayout,
                            }));
                        }else{
                            var chart = root.container.children.push(
                                am5percent.PieChart.new(root, {
                                radius: am5.percent(90),
                                layout: root.verticalLayout,
                            }));
                        }

                       var legend = chart.children.push(am5.Legend.new(root, {
                          centerX: am5.percent(50),
                          x: am5.percent(50),
                          layout: am5.GridLayout.new(root, {
                            maxColumns: 3,
                            fixedWidthGrid: true
                          }),
                          y: am5.percent(100),
                          centerY: am5.percent(100),
                          reverseChildren: true,
                        }));
                       if(isRtl){
                           legend.labels.template.setAll({
                               textAlign: "right",
//                               marginLeft: 5,
                           });
                           legend.itemContainers.template.setAll({
                                reverseChildren: true,
                                paddingLeft: 20,
                                paddingRight: 20,
                           });
                       }

                       for (let k = 0;k<ks_data.length ; k++){
                            series[k] = chart.series.push(
                                am5percent.PieSeries.new(root, {
                                name: `${ks_data[k].label}`,
                                valueField: `${ks_data[k].label}`,
                                categoryField: "category",
                                alignLabels: false,
                            })
                            );
                        }
                    }
                    var bgColor = root.interfaceColors.get("background");
                    for (let rec of series){
                        rec.ticks.template.setAll({ forceHidden: true })
                        rec.slices.template.setAll({
                            stroke: bgColor,
                            strokeWidth: 2,
                            templateField: "settings",
                        });
                        rec.slices.template.events.on("click", function(ev) {
                            rec.slices.each(function(slice) {
                                if(slice == ev.target && self.ks_dashboard_data && !self.ks_dashboard_data['ks_ai_dashboard'] && item.ks_data_calculation_type === 'custom'){
                                    self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                                }
                            })
                        });

                        if (item.ks_show_records == true){
                            var tooltip = am5.Tooltip.new(root, {
                                textAlign: "center",
                                centerX: am5.percent(96)
                            });
                            tooltip.label.setAll({
                                direction: "rtl"
                            })
                            rec.slices.template.setAll({
                                tooltipText: "[bold]{category}[/]\n{name}: {value}",
                                tooltip: tooltip
                            });
                        }
                        if (item.ks_show_data_value == true){
                            rec.labels.template.setAll({
                                text: item.ks_data_label_type == 'value'? "{value}":("{valuePercentTotal}%") ,
                                inside: true,
                                textType: data?.length>10? "radial" : "circular",
                                centerX: am5.percent(80)
                            })
                        }
                        else{
                            rec.labels.template.setAll({forceHidden:true})
                        }
                        rec.data.setAll(data)
                         if(item.ks_hide_legend == true && series){
                            legend.data.setAll(rec.dataItems);
                         }

                        rec.appear(1000, 100);
                    }
//                    legend.data.setAll(chart.series.values);

//                    root.rtl = true
                    break;
                case "ks_polarArea_chart":
                case "ks_radar_view":
                case "ks_flower_view":
                case "ks_radialBar_chart":
                    if(zooming_enabled){
                        var wheely_val = "zoomX";
                    }else{
                        var wheely_val = 'none';
                    }
                    var chart = root.container.children.push(am5radar.RadarChart.new(root, {
                        panX: false,
                        panY: false,
                        wheelX: "panX",
                        wheelY: wheely_val,
                        radius: am5.percent(80),
                        layout: root.verticalLayout,
                    }));

                    if (item.ks_dashboard_item_type == "ks_flower_view"){
                        var xRenderer = am5radar.AxisRendererCircular.new(root, {});
                        xRenderer.labels.template.setAll({
                            radius: 10,
                            cellStartLocation: 0.2,
                            cellEndLocation: 0.8
                        });
                    }else if (item.ks_dashboard_item_type == "ks_radialBar_chart"){
                        var xRenderer = am5radar.AxisRendererCircular.new(root, {
                            strokeOpacity: 0.1,
                            minGridDistance: 50
                         });
                        xRenderer.labels.template.setAll({
                            radius: 23,
                            maxPosition: 0.98
                        });
                    }else{
                        var xRenderer = am5radar.AxisRendererCircular.new(root, {});
                        xRenderer.labels.template.setAll({
                            radius: 10,
                        });
                    }
                    if (item.ks_dashboard_item_type == "ks_radialBar_chart"){
                        var xAxis = chart.xAxes.push(am5xy.ValueAxis.new(root, {
                            renderer: xRenderer,
                            extraMax: 0.1,
                            tooltip: am5.Tooltip.new(root, {})
                        }));

                        var yAxis = chart.yAxes.push(am5xy.CategoryAxis.new(root, {
                            categoryField: "category",
                            renderer: am5radar.AxisRendererRadial.new(root, { minGridDistance: 20 })
                        }));
                        yAxis.get("renderer").labels.template.setAll({
                            oversizedBehavior: "truncate",
                            textAlign: "center",
                            maxWidth: 150,
                            ellipsis: "..."
                        });
                    }else{
                        var xAxis = chart.xAxes.push(am5xy.CategoryAxis.new(root, {
                            maxDeviation: 0,
                            categoryField: "category",
                            renderer: xRenderer,
                            tooltip: am5.Tooltip.new(root, {})
                        }));
                        xAxis.data.setAll(data);

                        var yAxis = chart.yAxes.push(am5xy.ValueAxis.new(root, {
                            renderer: am5radar.AxisRendererRadial.new(root, {})
                        }));
                    }
                    if (item.ks_dashboard_item_type == "ks_polarArea_chart"){
                        for (let k = 0;k<ks_data.length ; k++) {
                            var series = chart.series.push(am5radar.RadarColumnSeries.new(root, {
                                stacked: true,
                                name: `${ks_data[k].label}`,
                                xAxis: xAxis,
                                yAxis: yAxis,
                                valueYField: `${ks_data[k].label}`,
                                categoryXField: "category",
                                alignLabels: true,
                            }));

                        series.set("stroke", root.interfaceColors.get("background"));
                        if (item.ks_show_records == true){
                            var tooltip = am5.Tooltip.new(root, {
                                textAlign: "center",
                                centerX: am5.percent(96)
                            });
                            tooltip.label.setAll({
                                direction: "rtl"
                            })
                            series.columns.template.setAll({
                                width: am5.p100,
                                strokeOpacity: 0.1,
                                tooltipText: "{name}: {valueY}",
                                tooltip: tooltip
                            });
                        }
                        series.columns.template.events.on("click",function(ev){
                            if (item.ks_data_calculation_type === 'custom' && self.ks_dashboard_data && !self.ks_dashboard_data['ks_ai_dashboard']){
                                self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                            }
                        });
                        series.data.setAll(data);
                        }
                        xAxis.data.setAll(data);
                    }else if (item.ks_dashboard_item_type == "ks_flower_view"){
                        for (let k = 0;k<ks_data.length ; k++){
                            var series = chart.series.push(
                                am5radar.RadarColumnSeries.new(root, {
                                name: `${ks_data[k].label}`,
                                xAxis: xAxis,
                                yAxis: yAxis,
                                valueYField: `${ks_data[k].label}`,
                                categoryXField: "category"
                             })
                            );

                            var tooltip = am5.Tooltip.new(root, {
                                textAlign: "center",
                                centerX: am5.percent(96)
                            });
                            tooltip.label.setAll({
                                direction: "rtl"
                            })

                            series.columns.template.setAll({
                                tooltip: tooltip,
                                tooltipText: "{name}: {valueY}",
                                width: am5.percent(100)
                            });
                            series.columns.template.events.on("click",function(ev){
                                if (item.ks_data_calculation_type === 'custom' && self.ks_dashboard_data && !self.ks_dashboard_data['ks_ai_dashboard']){
                                    self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                                }
                            });
                            series.data.setAll(data);
                        }

                    }else if (item.ks_dashboard_item_type == "ks_radialBar_chart"){
                        for (let k = 0;k<ks_data.length ; k++) {
                            var series = chart.series.push(am5radar.RadarColumnSeries.new(root, {
                                stacked: true,
                                name: `${ks_data[k].label}`,
                                xAxis: xAxis,
                                yAxis: yAxis,
                                valueXField: `${ks_data[k].label}`,
                                categoryYField: "category"
                            }));

                            series.set("stroke",root.interfaceColors.get("background"));
                            var tooltip = am5.Tooltip.new(root, {
                                textAlign: "center",
                                centerX: am5.percent(96)
                            });
                            tooltip.label.setAll({
                                direction: "rtl"
                            })

                            series.columns.template.setAll({
                                width: am5.p100,
                                strokeOpacity: 0.1,
                                tooltipText: "{name}: {valueX}  {category}",
                                tooltip: tooltip
                            });
                            series.columns.template.events.on("click",function(ev){
                                if (item.ks_data_calculation_type === 'custom' && self.ks_dashboard_data && !self.ks_dashboard_data['ks_ai_dashboard']){
                                    self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                                }
                            });
                            series.data.setAll(data);
                        }
                        yAxis.data.setAll(data);
                   }else{
                        for (let k = 0;k<ks_data.length ; k++){
                            var tooltip = am5.Tooltip.new(root, {
                                textAlign: "center",
                                centerX: am5.percent(96),
                                labelText: "{valueY}"
                            });
                            tooltip.label.setAll({
                                direction: "rtl"
                            })
                            var series = chart.series.push(am5radar.RadarLineSeries.new(root, {
                                name:`${ks_data[k].label}`,
                                xAxis: xAxis,
                                yAxis: yAxis,
                                valueYField: `${ks_data[k].label}`,
                                categoryXField: "category",
                                alignLabels: true,
                                tooltip: tooltip
                            }));

                            series.strokes.template.setAll({
                            strokeWidth: 2,

                            });
                        series.bullets.push(function() {
                            var graphics = am5.Circle.new(root, {
                                fill: series.get("fill"),
                                radius: 5
                            });
                            graphics.events.on("click", function(ev) {
                                if (item.ks_data_calculation_type === 'custom' && self.ks_dashboard_data && !self.ks_dashboard_data['ks_ai_dashboard']){
                                    self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                                }
                            });
                            return am5.Bullet.new(root, {
                                sprite: graphics
                            });
                        });
                        series.data.setAll(data);
                    }
                        xAxis.data.setAll(data);
                   }

                    break;

                case "ks_scatter_chart":
                if(zooming_enabled){
                        var wheely_val = "zoomX";
                    }else{
                        var wheely_val = 'none';
                    }
                var chart = root.container.children.push(am5xy.XYChart.new(root, {panX: false,panY: false,
                 wheelX: "panX",wheelY: wheely_val,layout: root.verticalLayout}));
                    var xAxis = chart.xAxes.push(am5xy.ValueAxis.new(root, {
                        renderer: am5xy.AxisRendererX.new(root, { minGridDistance: 50 }),
                        tooltip: am5.Tooltip.new(root, {})
                    }));
                    xAxis.ghostLabel.set("forceHidden", true);

                    var yAxis = chart.yAxes.push(am5xy.ValueAxis.new(root, {
                        renderer: am5xy.AxisRendererY.new(root, {}),
                        tooltip: am5.Tooltip.new(root, {})
                    }));
                    yAxis.ghostLabel.set("forceHidden", true);

                    var tooltip = am5.Tooltip.new(root, {
                        textAlign: "center",
                        centerX: am5.percent(96),
                        labelText: "{name_1}:{valueX} {name}:{valueY}"
                    });
                    tooltip.label.setAll({
                            direction: "rtl"
                    })

                    for (let k = 0;k<ks_data.length ; k++){
                        var series = chart.series.push(am5xy.LineSeries.new(root, {
                            name:`${ks_data[k].label}`,
                            name_1 : chart_data.groupby,
                            calculateAggregates: true,
                            xAxis: xAxis,
                            yAxis: yAxis,
                            valueYField: `${ks_data[k].label}`,
                            valueXField: "category",
                            tooltip: tooltip
                        }));

                        series.bullets.push(function() {
                            var graphics = am5.Triangle.new(root, {
                                fill: series.get("fill"),
                                width: 10,
                                height: 7
                            });
                            graphics.events.on("click", function(ev) {
                                if (item.ks_data_calculation_type === 'custom' && self.ks_dashboard_data && !self.ks_dashboard_data['ks_ai_dashboard']){
                                    self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                                }
                            });
                            return am5.Bullet.new(root, {
                                sprite: graphics
                            });
                        });
                         var cursor = chart.set("cursor", am5xy.XYCursor.new(root, {
                            behavior: "none",
                            snapToSeries: [series]
                            }));
                            cursor.lineY.set("forceHidden", true);
                            cursor.lineX.set("forceHidden", true);
                        series.strokes.template.set("strokeOpacity", 0);
                        series.data.setAll(data);

                    }
                    break;
            }
//            if(chart_type == 'ks_radar_view'|| chart_type == 'ks_radialBar_chart'|| chart_type == 'ks_flower_view'|| chart_type == 'ks_polarArea_chart'){
            root.rtl=true;
            var legend = chart.children.push(
                am5.Legend.new(root, {
                    centerX: am5.p50,
                    x: am5.p50,
                    layout: root.gridLayout,
                    y: am5.percent(100),
                    centerY: am5.percent(100),
//                    ...(isRtl && {direction: "rtl"}),
                })
            );

            legend.labels.template.setAll({
                textAlign: "right",
                marginRight:5,
//                ...(isRtl && {direction: "rtl"}),
            });
            legend.itemContainers.template.setAll({
                reverseChildren: true,
            });

            if(item.ks_hide_legend == true && series && chart_type != 'ks_pie_chart' && chart_type != 'ks_doughnut_chart'){
                legend.data.setAll(chart.series.values);
            }


            if (item.ks_data_format && item.ks_data_format == 'global'){
                root.numberFormatter.setAll({
                    numberFormat: "#.0a",
                    bigNumberPrefixes: [{"number":1e+3,"suffix":"k"},{ "number": 1e+6, "suffix": "M" },
                    { "number": 1e+9, "suffix": "G" },{ "number": 1e+12, "suffix": "T" },
                    { "number": 1e+15, "suffix": "P" },{ "number": 1e+18, "suffix": "E" }]
                });
            }else if (item.ks_data_format && item.ks_data_format == 'indian'){
                root.numberFormatter.setAll({
                    numberFormat: "#.0a",
                    bigNumberPrefixes: [{"number":1e+3,"suffix":"Th"},{"number":1e+5,"suffix":"Lakh"},
                    { "number": 1e+7, "suffix": "Cr" },{ "number": 1e+9, "suffix": "Arab" }],
                });
            }else if (item.ks_data_format && item.ks_data_format == 'colombian'){
                root.numberFormatter.setAll({
                    numberFormat: "#.a",
                    bigNumberPrefixes: [{"number":1e+6,"suffix":"M"},{ "number": 1e+9, "suffix": "M" },{ "number": 1e+12, "suffix": "M" },
                    { "number": 1e+15, "suffix": "M" },{ "number": 1e+18, "suffix": "M" }]
                });
            }else{
                root.numberFormatter.setAll({
                    numberFormat: "#"
                });
            }
            chart.appear(1000, 100);

            if (item.ks_dashboard_item_type != 'ks_pie_chart' &&  item.ks_dashboard_item_type != 'ks_doughnut_chart' && series){
                series.appear();
            }
            $ks_gridstack_container.find('.ks_li_' + item.ks_chart_item_color).addClass('global-active');
        }else{
            view === 'dashboard_view' ? $ks_gridstack_container.find('.ks_chart_card_body').append(renderToString("ksNoItemChartView", {})) : $ks_gridstack_container.append(renderToString("ksNoItemChartView", {}))
        }
    }else{
            view === 'dashboard_view' ? $ks_gridstack_container.find('.ks_chart_card_body').append(renderToString("ksNoItemChartView", {})) : $ks_gridstack_container.append(renderToString("ksNoItemChartView", {}))
        }
    }
    catch(e){
        console.error("Chart doesn't rendered")
    }
}

export function ksrenderfunnelchart($ks_gridstack_container, item, view){
            var self =this;
            const isRtl = localization.direction === "rtl"
            if(view === 'dashboard_view'){
                if($ks_gridstack_container.find('.ks_chart_card_body').length){
                    var funnelRender = $ks_gridstack_container.find('.ks_chart_card_body')[0];
                }else{
                    $($ks_gridstack_container.find('.ks_dashboarditem_chart_container')[0]).append("<div class='card-body ks_chart_card_body'>");
                    var funnelRender = $ks_gridstack_container.find('.ks_chart_card_body')[0];
                }
            }
            else if(view === 'preview'){
                if($ks_gridstack_container.find(".graph_text").length){
                    $ks_gridstack_container.find(".graph_text").remove();
                }
                var funnelRender = $ks_gridstack_container[0];
            }
            var funnel_data = JSON.parse(item.ks_chart_data);
            try{
                if (funnel_data['labels'] && funnel_data['datasets'].length){
                var ks_labels = funnel_data['labels'];
                var ks_data = funnel_data.datasets[0].data;
                const ks_sortobj = Object.fromEntries(
                                                ks_labels.map((key, index) => [key, ks_data[index]]),
                                            );
                const keyValueArray = Object.entries(ks_sortobj);
                keyValueArray.sort((a, b) => b[1] - a[1]);

                var data=[];
                if (keyValueArray.length){
                    for (let i=0 ; i<keyValueArray.length ; i++){
                    data.push({"stage":keyValueArray[i][0],"applicants":keyValueArray[i][1]})
                    }
                    const root = am5.Root.new(funnelRender);
                    this.root = root
                    const theme = item.ks_chart_item_color
                    switch(theme){
                    case "default":
                        root.setThemes([am5themes_Animated.new(root)]);
                        break;
                    case "dark":
                        root.setThemes([am5themes_Dataviz.new(root)]);
                        break;
                    case "material":
                        root.setThemes([am5themes_Material.new(root)]);
                        break;
                    case "moonrise":
                        root.setThemes([am5themes_Moonrise.new(root)]);
                        break;
                    };

                    var chart = root.container.children.push(
                        am5percent.SlicedChart.new(root, {
                            layout: root.verticalLayout
                        })
                    );
                    // Create series
                    var series = chart.series.push(
                        am5percent.FunnelSeries.new(root, {
                            alignLabels: false,
                            name: "Series",
                            valueField: "applicants",
                            categoryField: "stage",
                            orientation: "vertical",
                        })
                    );
                    series.data.setAll(data);
                     series.appear(1000);
                    if(item.ks_show_data_value && item.ks_data_label_type=="value"){
                        series.labels.template.set("text", "{value.formatNumber('0.00')}");
                    }else if(item.ks_show_data_value && item.ks_data_label_type=="percent"){
                        series.labels.template.set("text", "{valuePercentTotal.formatNumber('0.00')}%");
                    }else{
                        series.ticks.template.set("forceHidden", true);
                        series.labels.template.set("forceHidden", true);
                    }
                    var legend = chart.children.push(
                        am5.Legend.new(root, {
                            centerX: am5.p50,
                            x: am5.p50,
//                            marginTop: 15,
//                            marginBottom: 15,
                            layout: am5.GridLayout.new(root, {
                                maxColumns: 3,
                                fixedWidthGrid: true
                            }),
                            y: am5.percent(100),
                            centerY: am5.percent(100),
                            reverseChildren: true,
                        })
                    );
                    if(isRtl){
                           legend.labels.template.setAll({
                               textAlign: "right",
                               marginRight: 5
                           });
                           legend.itemContainers.template.setAll({
                                reverseChildren: true,
                                paddingLeft: 20,
                                paddingRight: 20,
                           });
                   }
                    if(item.ks_hide_legend==true){
                        legend.data.setAll(series.dataItems);
                    }
                    chart.appear(1000, 100);

                    if(!this.chart_container){
                        this.chart_container = {};
                    }
                    this.chart_container[item.id] = chart;
                    series.slices._values.forEach((rec)=>{
                        rec.events.on("click",function(ev){
                            if (item.ks_data_calculation_type === 'custom' && self.ks_dashboard_data && !self.ks_dashboard_data['ks_ai_dashboard']){
                                self.onChartCanvasClick_funnel(ev,`${item.id}`, item)
                            }
                        })
                    })
                    $ks_gridstack_container.find('.ks_li_' + item.ks_chart_item_color).addClass('global-active');
                }else{
                    view === 'dashboard_view' ? $ks_gridstack_container.find('.ks_chart_card_body').append(renderToString("ksNoItemChartView", {})) :
                    $ks_gridstack_container.append(renderToString("ksNoItemChartView", {}))
                }
            }else{
                    view === 'dashboard_view' ? $ks_gridstack_container.find('.ks_chart_card_body').append(renderToString("ksNoItemChartView", {})) :
                    $ks_gridstack_container.append(renderToString("ksNoItemChartView", {}))
                }
                return $ks_gridstack_container;
            }
            catch(e){
                console.error("Chart doesn't rendered")
            }
     }

export async function ksrendermapview($ks_map_view_tmpl, item, view){
        try{
            const isRtl = localization.direction === "rtl"
            var self =this;
            if(view === 'dashboard_view'){
                if($ks_map_view_tmpl.find('.ks_chart_card_body').length){
                    var mapRender = $ks_map_view_tmpl.find('.ks_chart_card_body')[0];
                }else{
                    $($ks_map_view_tmpl.find('.ks_dashboarditem_chart_container')[0]).append("<div class='card-body ks_chart_card_body'>");
                    var mapRender = $ks_map_view_tmpl.find('.ks_chart_card_body')[0];
                }
            }
            else if(view === 'preview'){
                if($ks_map_view_tmpl.find(".graph_text").length){
                    $ks_map_view_tmpl.find(".graph_text").remove();
                }
                var mapRender = $ks_map_view_tmpl[0];
            }
            var map_data = JSON.parse(item.ks_chart_data);
            var ks_data=[];
            let data = [];
            let label_data = [];
            let query_label_data = [];
            let domain = [];
            let partner_domain = [];
            var partners = [];
            if (map_data.groupByIds?.length){
                partners = map_data['partner']
            var partners_query = [];
            partners_query = map_data['ks_partners_map']
            var ks_labels = map_data['labels'];
            if (map_data.datasets.length){
                var ks_data = map_data.datasets[0].data;
            }
            if (item.ks_data_calculation_type === 'query'){
                for (let i=0 ; i<ks_labels.length ; i++){
                    if (ks_labels[i] !== false){
                        if (typeof ks_labels[i] == 'string'){
                            if (ks_labels[i].includes(',')){
                                ks_labels[i] = ks_labels[i].split(', ')[1]
                            }
                            query_label_data.push(ks_labels[i])
                        }else{
                            query_label_data.push(ks_labels[i])
                        }
                    }
                }
                for (let i=0 ; i<query_label_data.length ; i++){
                    if (typeof query_label_data[i] == 'string'){
                        for (let j=0 ; j<partners_query.length ; j++){
                            if (query_label_data[i] == partners_query[j].name){
                                data.push({"title":query_label_data[i], "latitude":partners_query[j].partner_latitude, "longitude": partners_query[j].partner_longitude});
                            }
                        }
                    }else{
                          data.push({"title":query_label_data[i], "latitude":partners_query[i].partner_latitude, "longitude": partners_query[i].partner_longitude});
                    }
                }
            }
            if (ks_data.length && ks_labels.length){
                if (item.ks_data_calculation_type !== 'query'){
                    for (let i=0 ; i<ks_labels.length ; i++){
                        if (ks_labels[i] !== false){
                            if (ks_labels[i].includes(',')){
                                ks_labels[i] = ks_labels[i].split(', ')[1]
                            }
                            label_data.push({'title': ks_labels[i], 'value':ks_data[i]})
                        }
                    }
                    for (let i=0 ; i<label_data.length ; i++){
                        for (let j=0 ; j<partners.length ; j++){
                            if (label_data[i].title == partners[j].name){
                                partners[j].name = partners[j].name + ';' + label_data[i].value
                            }
                        }
                    }
                    for (let i=0 ; i<partners.length ; i++){
                        data.push({"title":partners[i].name, "latitude":partners[i].partner_latitude, "longitude": partners[i].partner_longitude});
                    }
                }
                const root = am5.Root.new(mapRender);
                this.root = root
                root.setThemes([am5themes_Animated.new(root)]);

                // Create the map chart
                var chart = root.container.children.push(
                  am5map.MapChart.new(root, {
                    panX: "translateX",
                    panY: "translateY",
                    projection: am5map.geoMercator()
                  })
                );

                var cont = chart.children.push(
                  am5.Container.new(root, {
                    layout: root.horizontalLayout,
                    x: 20,
                    y: 40
                  })
                );

                // Add labels and controls
                cont.children.push(
                  am5.Label.new(root, {
                    centerY: am5.p50,
                    text: "Map",
                    ...(isRtl && {direction: "rtl"})
                  })
                );

                var switchButton = cont.children.push(
                  am5.Button.new(root, {
                    themeTags: ["switch"],
                    centerY: am5.p50,
                    icon: am5.Circle.new(root, {
                      themeTags: ["icon"]
                    }),
                    ...(isRtl && {direction: "rtl"})
                  })
                );

                switchButton.on("active", function() {
                  if (!switchButton.get("active")) {
                    chart.set("projection", am5map.geoMercator());
                    chart.set("panY", "translateY");
                    chart.set("rotationY", 0);
                    backgroundSeries.mapPolygons.template.set("fillOpacity", 0);
                  } else {
                    chart.set("projection", am5map.geoOrthographic());
                    chart.set("panY", "rotateY");

                    backgroundSeries.mapPolygons.template.set("fillOpacity", 0.1);
                  }
                });

                cont.children.push(
                  am5.Label.new(root, {
                    centerY: am5.p50,
                    text: "Globe",
                    ...(isRtl && {direction: "rtl"})
                  })
                );

                // Create series for background fill
                var backgroundSeries = chart.series.push(am5map.MapPolygonSeries.new(root, {}));
                backgroundSeries.mapPolygons.template.setAll({
                  fill: root.interfaceColors.get("alternativeBackground"),
                  fillOpacity: 0,
                  strokeOpacity: 0
                });

                    // Add background polygon
                backgroundSeries.data.push({
                  geometry: am5map.getGeoRectangle(90, 180, -90, -180)
                });

                // Create main polygon series for countries
                var polygonSeries = chart.series.push(
                  am5map.MapPolygonSeries.new(root, {
                    geoJSON: am5geodata_worldLow,
                    exclude: ["AQ"]
                  })
                );
                polygonSeries.mapPolygons.template.setAll({
                  tooltipText: "{name}",
                  toggleKey: "active",
                  interactive: true
                });

                polygonSeries.mapPolygons.template.states.create("hover", {
                  fill: root.interfaceColors.get("primaryButtonHover")
                });

                polygonSeries.mapPolygons.template.states.create("active", {
                  fill: root.interfaceColors.get("primaryButtonHover")
                });

                var previousPolygon;

                polygonSeries.mapPolygons.template.on("active", function (active, target) {
                  if (previousPolygon && previousPolygon != target) {
                    previousPolygon.set("active", false);
                  }
                  if (target.get("active")) {
                    polygonSeries.zoomToDataItem(target.dataItem );
                  }
                  else {
                    chart.goHome();
                  }
                  previousPolygon = target;
                });

                // Create line series for trajectory lines
                var lineSeries = chart.series.push(am5map.MapLineSeries.new(root, {}));
                lineSeries.mapLines.template.setAll({
                  stroke: root.interfaceColors.get("alternativeBackground"),
                  strokeOpacity: 0.3
                });

                // Create point series for markers
                var pointSeries = chart.series.push(am5map.MapPointSeries.new(root, {}));
                var colorset = am5.ColorSet.new(root, {});
                const self = root;


                pointSeries.bullets.push(function() {
                  var container = am5.Container.new(self, {
                    tooltipText: "{title}",
                    cursorOverStyle: "pointer"
                  });

                  var circle = container.children.push(
                    am5.Circle.new(self, {
                      radius: 4,
                      tooltipY: 0,
                      fill: colorset.next(),
                      strokeOpacity: 0
                    })
                  );


                  var circle2 = container.children.push(
                    am5.Circle.new(self, {
                      radius: 4,
                      tooltipY: 0,
                      fill: colorset.next(),
                      strokeOpacity: 0,
                      tooltipText: "{title}"
                    })
                  );

                  circle.animate({
                    key: "scale",
                    from: 1,
                    to: 5,
                    duration: 600,
                    easing: am5.ease.out(am5.ease.cubic),
                    loops: Infinity
                  });

                  circle.animate({
                    key: "opacity",
                    from: 1,
                    to: 0.1,
                    duration: 600,
                    easing: am5.ease.out(am5.ease.cubic),
                    loops: Infinity
                  });

                  return am5.Bullet.new(self, {
                    sprite: container
                  });
                });

                for (var i = 0; i < data.length; i++) {
                  var final_data = data[i];
                  addCity(final_data.longitude, final_data.latitude, final_data.title);
                }
                function addCity(longitude, latitude, title) {
                  pointSeries.data.push({
                    geometry: { type: "Point", coordinates: [longitude, latitude] },
                    title: title,
                  });
                }

                // Add zoom control
                chart.set("zoomControl", am5map.ZoomControl.new(root, {}));

                // Set clicking on "water" to zoom out
                chart.chartContainer.get("background").events.on("click", function () {
                  chart.goHome();
                })

                // Make stuff animate on load
                chart.appear(1000, 100);
                if(view === 'dashboard_view')    this.chart_container[item.id] = chart;
    //               $ks_map_view_tmpl.find('.ks_li_' + item.ks_flower_item_color).addClass('ks_date_filter_selected');

            }else{
                view === 'dashboard_view' ? $ks_map_view_tmpl.find('.ks_chart_card_body').append(renderToString("ksNoItemChartView", {})) :
                    $ks_map_view_tmpl.append(renderToString("ksNoItemChartView", {}))
            }
            }else{
                view === 'dashboard_view' ? $ks_map_view_tmpl.find('.ks_chart_card_body').append(renderToString("ksNoItemChartView", {})) :
                    $ks_map_view_tmpl.append(renderToString("ksNoItemChartView", {}))
            }
                return $ks_map_view_tmpl;
        }
        catch(e){
            console.error("Chart doesn't rendered")
        }
    }