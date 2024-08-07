/** @odoo-module */
import { Order, Orderline, Payment } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { _t } from '@web/core/l10n/translation';
import { parseFloat as oParseFloat } from "@web/views/fields/parsers";
import {
    formatFloat,
    roundDecimals as round_di,
    roundPrecision as round_pr,
    floatIsZero,
} from "@web/core/utils/numbers";
patch(Order.prototype, {
  set_orderline_options(orderline, options) {
        super.set_orderline_options(...arguments);
        if(options.product_uom_id !== undefined){
            orderline.product_uom_id = options.product_uom_id;

        }
    }
});
patch(Orderline.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.product_uom_id = this.product.default_uom_id || this.product_uom_id || this.product.uom_id;

    },

    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.product_uom_id = this.product_uom_id[0];
        return json;
    },
    init_from_JSON(json) {
    super.init_from_JSON(...arguments);

    console.log('init_from_JSON:', json);

    // Ensure json.product_uom_id is valid and this.pos.units_by_id is properly initialized
    if (json.product_uom_id && this.pos && this.pos.units_by_id && this.pos.units_by_id[json.product_uom_id]) {
        this.product_uom_id = {
            0: this.pos.units_by_id[json.product_uom_id].id,
            1: this.pos.units_by_id[json.product_uom_id].name
        };
    } else {
        console.error('Invalid product_uom_id or units_by_id not found', json.product_uom_id, this.pos.units_by_id);
        // Handle the case where product_uom_id is not found, e.g., by setting a default value or showing an error message
        this.product_uom_id = null;  // or some default value
    }
},
    set_uom(uom_id) {
        this.product_uom_id = uom_id;
        const unit = this.get_unit();
    if (unit) {
        this.set_unit_price(unit.price);
    }
    },
    get_unit(){
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
    set_quantity(quantity, keep_price) {
        this.order.assert_editable();
        var quant =
            typeof quantity === "number" ? quantity : oParseFloat("" + (quantity ? quantity : 0));
        if (this.refunded_orderline_id in this.pos.toRefundLines) {
            const toRefundDetail = this.pos.toRefundLines[this.refunded_orderline_id];
            const maxQtyToRefund =
                toRefundDetail.orderline.qty - toRefundDetail.orderline.refundedQty;
            if (quant > 0 ) {
                if (!this.comboParent) {
                    this.env.services.popup.add(ErrorPopup, {
                        title: _t("Positive quantity not allowed"),
                        body: _t(
                            "Only a negative quantity is allowed for this refund line. Click on +/- to modify the quantity to be refunded."
                        ),
                    });
                }
                return false;
            } else if (quant == 0) {
                toRefundDetail.qty = 0;
            } else if (-quant <= maxQtyToRefund) {
                toRefundDetail.qty = -quant;
            } else {
                if(!this.comboParent){
                    this.env.services.popup.add(ErrorPopup, {
                        title: _t("Greater than allowed"),
                        body: _t(
                            "The requested quantity to be refunded is higher than the refundable quantity of %s.",
                            this.env.utils.formatProductQty(maxQtyToRefund)
                        ),
                    });
                }
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

        if (!keep_price && this.price_type === "original") {
            this.order.fix_tax_included_price(this);
        }
        return true;
    },
    set_partner(partner) {
        this.assert_editable();
        this.partner = partner;
    },

});
patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(...arguments);
            this.product_uom_price = loadedData['product.multi.uom.price'];
    }
});
