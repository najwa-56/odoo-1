/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class QuantityPopup extends Component {
    static template = "point_of_sale.QuantityPopup";

    setup() {
        // Initialize quantity in the component state
        this.quantity = useState({ value: 1 });
    }

    get quantity() {
        return this.quantity.value;
    }

    set quantity(value) {
        this.quantity.value = value;
    }

    onConfirm() {
        this.trigger('confirm', this.quantity); // Handle confirmation with the current quantity
    }

    onClose() {
        this.trigger('close'); // Handle close action
    }
}
