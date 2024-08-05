/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class QuantityPopup extends Component {
    static template = "point_of_sale.QuantityPopup";

    setup() {
        this.quantity = useState({ value: 1 }); // Define quantity as a reactive property
    }

    get quantity() {
        return this.quantity.value;
    }

    set quantity(value) {
        this.quantity.value = value;
    }

    onConfirm() {
        this.trigger('confirm', this.quantity); // or any method to handle confirmation
    }

    onClose() {
        this.trigger('close'); // or any method to handle closing
    }
}
