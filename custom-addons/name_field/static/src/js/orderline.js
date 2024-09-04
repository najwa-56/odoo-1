/** @odoo-module */

import { Orderline } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

//Patched Orderline for adding the field for display
patch(Orderline.prototype, {
    getDisplayData() {
        return {
            ...super.getDisplayData(),
            name_field: this.get_product().name_field,
        };
    },
});
