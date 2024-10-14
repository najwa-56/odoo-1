/** @odoo-module */

import { parseFloat as oParseFloat } from "@web/views/fields/parsers";

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
        this.em_uom_list = loadedData['product.multi.uom.price'];
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
        // Access the UOM list and match barcodes
        var pos_multi_op = this.pos.em_uom_list;
        var unit_price = 0;
        var uom_data_matched = false;
        let selected_uom_id = null;
        let selected_uom_name = null;

        // Get the product template ID
        let product_tmpl_id = product.product_tmpl_id;

        // Check if the product exists in pos_multi_op
        if (pos_multi_op[product_tmpl_id]) {
            let uomPrices = pos_multi_op[product_tmpl_id].uom_id;

            // Loop through the UOM data for the product
            Object.values(uomPrices).forEach(function(uom_data) {
                if (uom_data.barcodes.includes(code.base_code)) {
                    unit_price = uom_data.price;
                    uom_data_matched = true;
                    selected_uom_id = uom_data.id;
                    selected_uom_name = uom_data.name_field 

                    Object.assign(options, {
                        price: uom_data.price,
                        extras: {
                            wvproduct_uom: this.pos.units_by_id[uom_data.id],
                        },
                    });
                }
            }, this);
        }

        // If UOM barcode wasn't matched, fallback to original product barcode
        if (!uom_data_matched) {
            if (product.barcode === code.base_code) {
                unit_price = product.lst_price;
                selected_uom_id = product.uom_id[0];

                Object.assign(options, {
                    price: product.lst_price,
                    extras: {
                        wvproduct_uom: this.pos.units_by_id[product.uom_id[0]],  // The original UOM
                    },
                });
            }
        }

        // Add the product to the order with the updated options
        this.currentOrder.add_product(product, options);

        // Set the unit price and UoM for the orderline
        var line = this.currentOrder.selected_orderline;
        line.set_unit_price(unit_price);
        line.set_product_uom(selected_uom_id);
        line.set_uom(selected_uom_id);  // Set UoM explicitly
        line.set_uom_name(selected_uom_name);
        line.price_manually_set = true;
        line.price_type = "automatic";

        this.numberBuffer.reset();
    }
});

patch(Orderline.prototype, {
    setup() {
        super.setup(...arguments);
        // Initialize wvproduct_uom to null instead of an empty string
        this.wvproduct_uom = null;
        this.product_uom_id =  this.product_uom_id || this.product.uom_id;
    },

    set_product_uom(uom_id){
        this.wvproduct_uom = this.pos.units_by_id[uom_id] || null;
        // Trigger change if necessary
    },
    set_uom(uom_id) {
        this.product_uom_id = uom_id;
       
    },

    


    

    get_uom_unit(){
        if (this.product.default_uom_price > 0 & this.price_type == "original" & this.product.default_uom_id != false){
            this.price = this.product.default_uom_price;
        }
        if (this.product_uom_id){
            var unit_id = this.product_uom_id;
            if(!unit_id){
                return undefined;
            }
            unit_id = unit_id[0];
            if(!this.pos){
                return undefined;
            }
            return this.pos.units_by_id[unit_id];
        }
        return this.product.get_unit();
    },


    get_unit(){
        if(this.wvproduct_uom){
            var unit_id = this.product.uom_id;
            if(!unit_id){
                return undefined;
            }
            unit_id = unit_id[0];
            if(!this.pos){
                return undefined;
            }
            // Use wvproduct_uom if available, otherwise fallback to the product's default UoM
            return this.wvproduct_uom ? this.wvproduct_uom : this.pos.units_by_id[unit_id];
        }
        else{
            return this.get_uom_unit()

        }
    },

    set_quantity(quantity, keep_price) {

        
        keep_price = true
        this.order.assert_editable();
        var quant =
            typeof quantity === "number" ? quantity : oParseFloat("" + (quantity ? quantity : 0));
        if (this.refunded_orderline_id in this.pos.toRefundLines) {
            const toRefundDetail = this.pos.toRefundLines[this.refunded_orderline_id];
            const maxQtyToRefund =
                toRefundDetail.orderline.qty - toRefundDetail.orderline.refundedQty;
            if (quant > 0) {
                this.env.services.popup.add(ErrorPopup, {
                    title: _t("Positive quantity not allowed"),
                    body: _t(
                        "Only a negative quantity is allowed for this refund line. Click on +/- to modify the quantity to be refunded."
                    ),
                });
                return false;
            } else if (quant == 0) {
                toRefundDetail.qty = 0;
            } else if (-quant <= maxQtyToRefund) {
                toRefundDetail.qty = -quant;
            } else {
                this.env.services.popup.add(ErrorPopup, {
                    title: _t("Greater than allowed"),
                    body: _t(
                        "The requested quantity to be refunded is higher than the refundable quantity of %s.",
                        this.env.utils.formatProductQty(maxQtyToRefund)
                    ),
                });
                return false;
            }
        }
        var unit = this.get_unit();
        if (unit) {
            if (unit.rounding) {
                var decimals = this.pos.dp["Product Unit of Measure"];
                var rounding = Math.max(unit.rounding, Math.pow(10, -decimals));
                this.quantity = round_pr(quant, rounding);
                this.quantityStr = formatFloat(this.quantity, {
                    digits: [69, decimals],
                });
            } else {
                this.quantity = round_pr(quant, 1);
                this.quantityStr = this.quantity.toFixed(0);
            }
        } else {
            this.quantity = quant;
            this.quantityStr = "" + this.quantity;
        }

        // just like in sale.order changing the quantity will recompute the unit price
        if (!keep_price && this.price_type === "original") {
            this.set_unit_price(
                this.product.get_price(
                    this.order.pricelist,
                    this.get_quantity(),
                    this.get_price_extra()
                )
            );
            this.order.fix_tax_included_price(this);
        }
        return true;
    
    },

    // export_as_JSON(){
    //     var unit_id = this.product.uom_id;
    //     var json = super.export_as_JSON(...arguments);
    //     // Export the UoM used in the orderline
    //     json.product_uom = this.wvproduct_uom ? this.wvproduct_uom.id : unit_id[0];
    //     json.product_uom_id =  this.wvproduct_uom ? this.wvproduct_uom.id : unit_id[0]
    //     return json;
    // },
    export_as_JSON(){
        var unit_id = this.product.uom_id;
        var json = super.export_as_JSON(...arguments);
        
        function getSafeUomId(uom) {
            // If uom is a proxy or an object-like structure
            if (uom && typeof uom === 'object') {
                // If uom is a Proxy with target, safely access the id or first value
                return uom.id || uom[0];
            }
            return uom; // If it's a direct value, return as is
        }
    
        const productUomId = getSafeUomId(this.product_uom_id);
    
        const productUom = 
            productUomId || 
            (this.wvproduct_uom && this.wvproduct_uom.id) || 
            unit_id[0];
    
        json.product_uom = productUom;
        json.product_uom_id = productUom;
    
        return json;
    },

    init_from_JSON(json){
        super.init_from_JSON(...arguments);
        this.wvproduct_uom = this.pos.units_by_id[json.product_uom] || null;
    },

    can_be_merged_with(orderline) {
        var result = super.can_be_merged_with(...arguments);

        // Ensure that wvproduct_uom is properly initialized
        const current_uom = this.wvproduct_uom || '';
        const orderline_uom = orderline.wvproduct_uom || '';


        // If either UOM is not defined or empty, return the default result
        if (current_uom === '' || orderline_uom === '' || !current_uom || !orderline_uom) {
            return result;
        }

        // Compare the product name and UOM IDs

        if (this.full_product_name === orderline.full_product_name && current_uom.id === orderline_uom.id) {
            return true;
        } else if (this.full_product_name === orderline.full_product_name && current_uom.id !== orderline_uom.id) {
            return false;
        }

        return result;
    }
});


