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
            orderline.name_field = options.name_field;

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
                this.name_field = options.name_field || this.name_field || "";  // Ensure initialization
       //  this.reorderProduct();

    },


    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.product_uom_id = this.product_uom_id[0];
            json.name_field = this.name_field;  // Add this line


        return json;
    },
    init_from_JSON(json) {
    super.init_from_JSON(...arguments);
    this.name_field = json.name_field || "";  // Add this line

   // console.log('init_from_JSON:', json);

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
 // Method to reorder the product in the orderlines array
 //  reorderProduct() {
   //     if (!this.order) return;
     //   const existingOrderline = this.order.orderlines.find(line => line.product.id === this.product.id);
    //   if (existingOrderline) {
            // Move existing orderline to the end of the orderlines array
     //       this.order.orderlines = this.order.orderlines.filter(line => line !== existingOrderline);
     //       this.order.orderlines.push(existingOrderline);

      //  }
 //   },
    getDisplayData() {
        return {
            ...super.getDisplayData(),
            name_field: this.get_product().name_field,
        };
    },
    set_uom(uom_id) {
        this.product_uom_id = uom_id;
        //    console.log("uom_id set to:", this.product_uom_id);

        const unit = this.get_unit();
    if (unit) {
        this.set_unit_price(unit.price);
        this.set_uom_name(unit.name_field)
    }
    },
    set_uom_name(uom_name) {
        this.name_field = uom_name;
  //  console.log("name_field set to:", this.name_field);

    },


    get_unit(){
        if (this.product.default_uom_price > 0 & this.price_type == "original" & this.product.default_uom_id != false){
            this.price = this.product.default_uom_price;
        }
        if (this.wvproduct_uom){
            var unit_id = this.wvproduct_uom;
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
        var quant =typeof quantity === "number" ? quantity : oParseFloat("" + (quantity ? quantity : 0));

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
patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(...arguments);
            this.product_uom_price = loadedData['product.multi.uom.price'];
    },

});

