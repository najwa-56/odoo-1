import { Component, useState } from "@odoo/owl";

export class QuantityPopup extends Component {
    static template = "point_of_sale.QuantityPopup";

    setup() {
        // Define quantity as a reactive state
        this.state = useState({ quantity: 1 });
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
