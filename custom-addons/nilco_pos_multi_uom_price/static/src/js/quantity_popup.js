/** @odoo-module */
import { Component, useState } from "@odoo/owl";
import { _t } from '@web/core/l10n/translation';

export class QuantityPopup extends Component {
    static template = "point_of_sale.QuantityPopup";

    setup() {
        this.state = useState({ quantity: 1 });
        this._t = _t; // Ensure _t is assigned correctly
    }

    get quantity() {
        return this.state.quantity;
    }

    set quantity(value) {
        this.state.quantity = value;
    }

    onConfirm() {
        this.trigger('confirm', this.quantity); // Handle confirmation
    }

    onClose() {
        this.trigger('close'); // Handle close action
    }
}
