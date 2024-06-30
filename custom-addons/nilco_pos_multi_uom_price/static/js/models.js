/** @odoo-module */
import { Order, Orderline, Payment } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(Order.prototype, {
    set_orderline_options(orderline, options) {
        super.set_orderline_options(...arguments);
        if (options.product_uom_id !== undefined) {
            orderline.product_uom_id = options.product_uom_id;
        }
    }
});

patch(Orderline.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        // Initialize product_uom_id if not already set
        this.product_uom_id = this.product_uom_id || this.product.uom_id;
    },

    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        // Ensure product_uom_id exists before accessing its elements
        if (this.product_uom_id) {
            json.product_uom_id = this.product_uom_id[0]; // Assuming product_uom_id is an array
        }
        return json;
    },

    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        // Ensure json.product_uom_id is valid and this.pos.units_by_id is properly initialized
        if (json.product_uom_id && this.pos && this.pos.units_by_id) {
            this.product_uom_id = {
                0: this.pos.units_by_id[json.product_uom_id].id,
                1: this.pos.units_by_id[json.product_uom_id].name
            };
        }
    },

    set_uom(uom_id) {
        // Handle setting product_uom_id
        this.product_uom_id = uom_id;
    },

    get_unit() {
        if (this.product_uom_id) {
            var unit_id = this.product_uom_id;
            if (!unit_id) {
                return undefined;
            }
            unit_id = unit_id[0];
            if (!this.pos) {
                return undefined;
            }
            // Ensure pos.units_by_id is properly initialized
            return this.pos.units_by_id[unit_id];
        }
        // Fallback to product.get_unit() if product_uom_id is not set
        return this.product.get_unit();
    }
});

patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(...arguments);
        // Ensure loadedData contains 'product.multi.uom.price' and initialize this.product_uom_price accordingly
        this.product_uom_price = loadedData['product.multi.uom.price'];
    }
});
