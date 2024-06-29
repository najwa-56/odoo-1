/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ErrorBarcodePopup } from "@point_of_sale/app/barcode/error_popup/barcode_error_popup";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { _t } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { TextAreaPopup } from "@point_of_sale/app/utils/input_popups/textarea_popup";
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { onMounted, useRef, useState } from "@odoo/owl";
import { PosDB } from "@point_of_sale/app/store/db";
import { Order, Orderline, Payment } from "@point_of_sale/app/store/models";
import { TicketScreen } from 'point_of_sale.TicketScreen';
import {
    formatFloat,
    roundDecimals as round_di,
    roundPrecision as round_pr,
    floatIsZero,
} from "@web/core/utils/numbers";


patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.em_uom_list = loadedData['product.multi.uom'];
    },
});
patch(PosDB.prototype, {
    add_products(products) {
        super.add_products(...arguments);
            for(var i = 0, len = products.length; i < len; i++){
                var product = products[i];
                if(product.has_multi_uom && product.multi_uom_ids){
                    var barcode_list = $.parseJSON(product.new_barcode);
                    for(var k=0;k<barcode_list.length;k++){
                        this.product_by_barcode[barcode_list[k]] = product;
                    }
                }
            }
    }
});

patch(ProductScreen.prototype, {
    async _barcodeProductAction(code) {
        const product = await this._getProductByBarcode(code);
        if (!product) {
            return this.popup.add(ErrorBarcodePopup, { code: code.base_code });
        }
        const options = await product.getAddProductOptions(code);
        // Do not proceed on adding the product when no options is returned.
        // This is consistent with clickProduct.
        if (!options) {
            return;
        }

        // update the options depending on the type of the scanned code
        if (code.type === "price") {
            Object.assign(options, {
                price: code.value,
                extras: {
                    price_type: "manual",
                },
            });
        } else if (code.type === "weight" || code.type === "quantity") {
            Object.assign(options, {
                quantity: code.value,
                merge: false,
            });
        } else if (code.type === "discount") {
            Object.assign(options, {
                discount: code.value,
                merge: false,
            });
        }
         this.currentOrder.add_product(product, options);
            var line = this.currentOrder.get_last_orderline();
            var pos_multi_op = this.pos.em_uom_list;
            var is_multi_uom = false;
            var unit_price = 0;
            for(var i=0;i<pos_multi_op.length;i++){
                if(pos_multi_op[i].barcode == code.base_code){
                    unit_price = pos_multi_op[i].price;
                    is_multi_uom = true;
                    Object.assign(options, {
                        price: pos_multi_op[i].price,
                        extras: {
                            wvproduct_uom: this.pos.units_by_id[pos_multi_op[i].multi_uom_id[0]],
                        },
                    });
                }
            }
            this.currentOrder.add_product(product,  options)
            if(is_multi_uom){
                var line = this.currentOrder.selected_orderline;
                line.set_unit_price(unit_price);
            }
        this.numberBuffer.reset();
    }
});

patch(Orderline.prototype, {
    setup() {
        super.setup(...arguments);
            this.wvproduct_uom = '';
        },

    set_product_uom(uom_id){
        this.wvproduct_uom = this.pos.units_by_id[uom_id];
        // this.trigger('change',this);
    },

        get_unit(){
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



        export_as_JSON(){
            var unit_id = this.product.uom_id;
            var json = super.export_as_JSON(...arguments);
            json.product_uom = this.wvproduct_uom == '' ? unit_id[0] : this.wvproduct_uom.id;
            return json;
        },
        init_from_JSON(json){
            super.init_from_JSON(...arguments);
            this.wvproduct_uom = json.wvproduct_uom;
        },
        can_be_merged_with(orderline){
            var result = super.can_be_merged_with(...arguments);
            if(result && this.wvproduct_uom.id != orderline.wvproduct_uom.id){
                return false;
            }
            else{
                return result;
            }
        },
    can_be_merged_with(orderline){
        var price = parseFloat(round_di(this.price || 0, this.pos.dp['Product Price']).toFixed(this.pos.dp['Product Price']));
        var order_line_price = orderline.get_product().get_price(orderline.order.pricelist, this.get_quantity());
        order_line_price = round_di(orderline.compute_fixed_price(order_line_price), this.pos.currency.decimal_places);
        if( this.get_product().id !== orderline.get_product().id){    //only orderline of the same product can be merged
            return false;
        }else if(!this.get_unit() || !this.get_unit().is_pos_groupable){
            return false;
        }else if(this.get_discount() > 0){             // we don't merge discounted orderlines
            return false;
        }else if(!utils.float_is_zero(price - order_line_price - orderline.get_price_extra(),this.pos.currency.decimal_places)){
            if(this.wvproduct_uom || orderline.wvproduct_uom){
                if(this.product.tracking == 'lot' && (this.pos.picking_type.use_create_lots || this.pos.picking_type.use_existing_lots)) {
                    return false;
                }else if (this.description !== orderline.description) {
                    return false;
                }else if (orderline.get_customer_note() !== this.get_customer_note()) {
                    return false;
                } else if (this.refunded_orderline_id) {
                    return false;
                }
                else if(this.wvproduct_uom.id != orderline.wvproduct_uom.id){
                    return false;
                }
                else{
                    return true;
                }
            }
            else{
                return false;
            }
        }else if(this.product.tracking == 'lot' && (this.pos.picking_type.use_create_lots || this.pos.picking_type.use_existing_lots)) {
            return false;
        }else if (this.description !== orderline.description) {
            return false;
        }else if (orderline.get_customer_note() !== this.get_customer_note()) {
            return false;
        } else if (this.refunded_orderline_id) {
            return false;
        }
        else if(this.wvproduct_uom.id != orderline.wvproduct_uom.id){
            return false;
        }
        else{
            return true;
        }
    }
});

export class MulitUOMWidget extends AbstractAwaitablePopup {
    static template = "em_pos_multi_uom.MulitUOMWidget";
    static defaultProps = {
        confirmText: _t("Add"),
        cancelText: _t("Discard"),
        title: "",
        body: "",
    };

    /**
     * @param {Object} props
     * @param {string} props.startingValue
     */
    setup() {
        super.setup();
        this.state = useState({ inputValue: this.props.startingValue });
        // this.inputRef = useRef("input");
        // onMounted(this.onMounted);
    }
    multi_uom_button(event){
        // const value = $(event.target).html();
        var uom_id = $(event.target).data('uom_id');
        var price = $(event.target).data('price');
        var line = this.env.services.pos.get_order().get_selected_orderline();
        if(line){
            line.set_unit_price(price);
            line.set_product_uom(uom_id);
            line.price_manually_set = true;
        }
        this.cancel();
    }
}

export class ChangeUOMButton extends Component {
    static template = "em_pos_multi_uom.ChangeUOMButton";

    setup() {
        this.pos = usePos();
        this.popup = useService("popup");
    }
    async onClick() {
        const selectedOrderline = this.pos.get_order().get_selected_orderline();
        // FIXME POSREF can this happen? Shouldn't the orderline just be a prop?
        if (!selectedOrderline) {
            return;
        }
            var modifiers_list = [];
            var product = selectedOrderline.get_product();
            var em_uom_list = this.pos.em_uom_list;
            var multi_uom_ids = product.multi_uom_ids;
            for(var i=0;i<em_uom_list.length;i++){
                if(multi_uom_ids.indexOf(em_uom_list[i].id)>=0){
                    modifiers_list.push(em_uom_list[i]);
                }
            }
        const { confirmed, payload: inputNote } = await this.popup.add(MulitUOMWidget, {
            startingValue: selectedOrderline.get_customer_note(),
            title: _t("POS Multi UOM"),
            modifiers_list:modifiers_list,
        });

        // if (confirmed) {
        //     selectedOrderline.set_customer_note(inputNote);
        // }
    }
}

export class RefundButton extends Component {
    static template = "point_of_sale.RefundButton";

    setup() {
        this.pos = usePos();
    }
    click() {
        const order = this.pos.get_order();
        const partner = order.get_partner();
        const searchDetails = partner ? { fieldName: "PARTNER", searchTerm: partner.name } : {};
        this.pos.showScreen("TicketScreen", {
            ui: { filter: "SYNCED", searchDetails },
            destinationOrder: order,
            multiUomData: this.pos.em_uom_list, // Pass the multi UOM data
        });
    }
}

ProductScreen.addControlButton({
    component: ChangeUOMButton,
    condition: function() {
        return this.pos.config.allow_multi_uom;
    },
});
