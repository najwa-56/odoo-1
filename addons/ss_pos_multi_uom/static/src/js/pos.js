odoo.define('ss_pos_multi_uom', function (require) {
"use strict";

const PosComponent = require('point_of_sale.PosComponent');
const ProductScreen = require('point_of_sale.ProductScreen');
const Orderline = require('point_of_sale.Orderline');
const { useListener } = require('web.custom_hooks');
const Registries = require('point_of_sale.Registries');
const models = require('point_of_sale.models');
const { useState, useRef } = owl.hooks;
const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');

    models.load_fields('product.product',['has_multi_uom','allow_uoms','show_all_uom']);

    class MulitUOMWidget extends AbstractAwaitablePopup {
        multi_uom_button(uom_id,price){
            var line = this.env.pos.get_order().get_selected_orderline();
            if(line){
                line.set_unit_price(price);
                line.set_product_uom(uom_id);
            }
            this.cancel();
        }
    }
    MulitUOMWidget.template = 'MulitUOMWidget';

    Registries.Component.add(MulitUOMWidget);
    const PosResOrderline = (Orderline) =>
        class extends Orderline {
            constructor() {
                super(...arguments);
                useListener('change_uom_order_line', this.change_uom_order_line);
            }
            async change_uom_order_line() { 
                var self = this;
                const order = this.env.pos.get_order();
                var selectedOrderLine = this.props.line;
                var product = selectedOrderLine.get_product();
                var modifiers_list = [];
                var orderline = selectedOrderLine;
                var units_by_id = self.env.pos.units_by_id;
                for(var key in units_by_id){
                    if(units_by_id[key].category_id[0]===orderline.get_unit().category_id[0]){
                        if(product.show_all_uom){
                            var price=orderline.price*orderline.get_unit().factor/units_by_id[key].factor;
                            modifiers_list.push({id:units_by_id[key].id,name:units_by_id[key].display_name,price:price,factor_inv:units_by_id[key].factor_inv});
                        }
                        else{
                            if($.inArray( self.env.pos.units_by_id[key].id, product.allow_uoms ) >= 0){
                                var price=orderline.price*orderline.get_unit().factor/self.env.pos.units_by_id[key].factor;
                                modifiers_list.push({id:units_by_id[key].id,name:units_by_id[key].display_name,price:price,factor_inv:units_by_id[key].factor_inv});
                            }
                        }
                    }
                }            
                await this.showPopup('MulitUOMWidget', {
                    title: this.env._t(' POS Multi UOM '),
                    ss_uom_list:modifiers_list,
                    product:product,
                });
            }
        }
    Registries.Component.extend(Orderline, PosResOrderline);
    
    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function(attr, options) {
            _super_orderline.initialize.call(this,attr,options);
            this.wvproduct_uom = '';
        },
        set_product_uom: function(uom_id){
            this.wvproduct_uom = this.pos.units_by_id[uom_id];
            this.trigger('change',this);
        },
        get_unit: function(){
            var unit_id = this.product.uom_id;
            if(!unit_id){
                return undefined;
            }
            unit_id = unit_id[0];
            if(!this.pos){
                return undefined;
            }
            return this.wvproduct_uom == '' ? this.pos.units_by_id[unit_id] : this.wvproduct_uom;
        },
        export_as_JSON: function(){
            var unit_id = this.product.uom_id;
            var json = _super_orderline.export_as_JSON.call(this);
            json.product_uom = this.wvproduct_uom == '' ? unit_id.id : this.wvproduct_uom.id;
            return json;
        },
        init_from_JSON: function(json){
            _super_orderline.init_from_JSON.apply(this,arguments);
            this.wvproduct_uom = json.wvproduct_uom;
        },

    });

});

