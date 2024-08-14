/** @odoo-module */
import { Order, Orderline, Payment } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { _t } from '@web/core/l10n/translation';
import { useService } from "@web/core/utils/hooks";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { reactive, Component, onMounted, onWillStart } from "@odoo/owl";
import { session } from "@web/session";
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
    },
     async load_product_multi_uom_prices() {
            try {
                const data = await this.rpc({
                    model: 'product.multi.uom.price',
                    method: 'search_read',
                    fields: ['id', 'uom_id', 'price','name_field'],
                    domain: [],  // Modify domain as needed
                });
                this.db.load_product_multi_uom_prices(data);
            } catch (error) {
                console.error('Error loading product_multi_uom_prices:', error);
            }
        },
      set_pricelist(pricelist) {

        var self = this;
        this.pricelist = pricelist;

        const orderlines = this.get_orderlines();

        const lines_to_recompute = orderlines.filter(
            (line) =>
                line.price_type === "original" && !(line.comboLines?.length || line.comboParent)
        );
        const combo_parent_lines = orderlines.filter(
            (line) => line.price_type === "original" && line.comboLines?.length
        );
        const attributes_prices = {};
        combo_parent_lines.forEach((parentLine) => {
            attributes_prices[parentLine.id] = this.compute_child_lines(
                parentLine.product,
                parentLine.comboLines.map((childLine) => {
                    const comboLineCopy = { ...childLine.comboLine };
                    if (childLine.attribute_value_ids) {
                        comboLineCopy.configuration = {
                            attribute_value_ids: childLine.attribute_value_ids,
                        };
                    }
                    return comboLineCopy;
                }),
                pricelist
            );
        });
        const combo_children_lines = orderlines.filter(
            (line) => line.price_type === "original" && line.comboParent
        );
    },
});
patch(Orderline.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.product_uom_id = this.product.default_uom_id || this.product_uom_id || this.product.uom_id;
                    this._update_sales_multi_uom_id();


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
  _update_sales_multi_uom_id() {
            if (this.product_uom_id) {
                const uom_id = this.product_uom_id[0];
                const uom = this.pos.units_by_id[uom_id];
                if (uom) {            console.log('Available multi_uom_prices:', this.pos.db.product_multi_uom_prices);

                    // Use the available data in the POS cache
                    const all_multi_uom_prices = this.pos.db.product_multi_uom_prices || [];
                                console.log('Filtered multi_uom_prices:', all_multi_uom_prices);

                    const matchingUOMs = all_multi_uom_prices.filter(uom_price => uom_price.uom_id === uom_id);
                                console.log('Matching UOMs:', matchingUOMs);

                    this.sales_multi_uom_id = matchingUOMs.length > 0 ? matchingUOMs[0].id : null;
                } else {
                    this.sales_multi_uom_id = null;
                }
            }
        },

    set_uom(uom_id) {
        this.product_uom_id = uom_id;
            this._update_sales_multi_uom_id();
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

 if (quant === 0 && zero1==true) {
        if (!this.comboParent) {
            this.env.services.popup.add(ErrorPopup, {
                title: _t("Quantity cannot be zero"),
                body: _t("Setting the quantity to zero is not allowed. Please enter a valid quantity."),
            });
        }
        return false;
    }
        // Handle refund logic

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
            // Handle unit of measure rounding

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
    }

});
var zero1=false;
patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(...arguments);
            this.product_uom_price = loadedData['product.multi.uom.price'];
    await this.user_groups1();
    },
    async user_groups1(){
     console.log('user_groups method is being called');
      try {
            const output = await this.orm.call(
                "pos.session",
                "pos_active_user_group2",
                [ , this.user]
            );

            zero1 = output.zero1;
            console.log('Value of zero1:', zero1);
        } catch (error) {
            console.error('Error in user_groups method:', error);
        }
    }
}
patch(DB.PosDB.prototype, {
    init(options) {
        this._super.apply(this, arguments);
                    this.product_uom_price = [];

    },
     load_product_multi_uom_prices(data) {
            this.product_uom_price = data;
        },

    },


);

