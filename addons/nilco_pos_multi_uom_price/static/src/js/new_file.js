/* @odoo-module */

import { patch } from "@web/core/utils/patch";
import { Order } from "@point_of_sale/models";

patch(Order.prototype, "MoveProductToEnd", {
    add_product(product, options) {
        super.add_product(...arguments);

        const selectedLine = this.get_selected_orderline();
        if (selectedLine) {
            const orderlines = this.orderlines.models;
            const index = orderlines.indexOf(selectedLine);

            if (index !== -1) {
                orderlines.splice(index, 1); // Remove the orderline from its current position
                orderlines.push(selectedLine); // Add the orderline to the end of the list

                this.trigger('change', this); // Trigger a change to re-render the order
                this.select_orderline(selectedLine); // Re-select the orderline
            }
        }
    },
});