/** @odoo-module */


import { patch } from "@web/core/utils/patch";
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
import { ErrorBarcodePopup } from "@point_of_sale/app/barcode/error_popup/barcode_error_popup";

import {
    formatFloat,
    roundDecimals as round_di,
    roundPrecision as round_pr,
    floatIsZero,
} from "@web/core/utils/numbers";

patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.multi_barcode_options = loadedData['pos.multi.barcode.options'];
    },
});

export class MulitUOMWidget extends AbstractAwaitablePopup {
    static template = "pos.multi.barcode.options.MulitUOMWidget";
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
    static template = "pos.multi.barcode.options.ChangeUOMButton";

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
            var wv_uom_list = this.pos.wv_uom_list;
            var multi_uom_ids = product.multi_uom_ids;
            for(var i=0;i<wv_uom_list.length;i++){
                if(multi_uom_ids.indexOf(wv_uom_list[i].id)>=0){
                    modifiers_list.push(wv_uom_list[i]);
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
patch(PosDB.prototype, {
    add_products(products) {
        var self = this;
        super.add_products(...arguments);
            for(var i = 0, len = products.length; i < len; i++){
                var product = products[i];
                if(product.pos_multi_barcode_option){
                    var barcode_list = $.parseJSON(product.barcode_options);
                    for(var k=0;k<barcode_list.length;k++){
                        this.product_by_barcode[barcode_list[k]] = product;
                    }
                }
            }
    }
});

ProductScreen.addControlButton({
    component: ChangeUOMButton,
    condition: function() {
        return this.pos.config.allow_multi_uom;
    },
});

patch(Orderline.prototype, {
    setup() {
        super.setup(...arguments);
            this.new_uom = '';
        },
        set_pro_uom(uom_id){
            this.new_uom = this.pos.units_by_id[uom_id];
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
            return this.new_uom == '' ? this.pos.units_by_id[unit_id] : this.new_uom;
        },

        export_as_JSON(){
            var unit_id = this.product.uom_id;
            var json = super.export_as_JSON(...arguments);
            json.product_uom = this.new_uom == '' ? unit_id[0] : this.new_uom.id;
            return json;
        },
        init_from_JSON(json){
            super.init_from_JSON(...arguments);
            this.new_uom = json.new_uom;
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
            var pos_multi_op = this.pos.multi_barcode_options;
            for(var i=0;i<pos_multi_op.length;i++){
                if(pos_multi_op[i].name == code.code){
                    line.set_quantity(pos_multi_op[i].qty);
                    line.set_unit_price(pos_multi_op[i].price);
                    line.set_pro_uom(pos_multi_op[i].unit[0]);
                    line.price_manually_set = true;
                }
            }
        this.numberBuffer.reset();
    }
});
