/** @odoo-module **/
import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class QuantityPopup extends Component {
    static template = "point_of_sale.QuantityPopup";

    setup() {
        super.setup();
        this.quantity = 1; // Default value
    }

    onClose() {
        this.env.services.popup.close();
    }

    onConfirm() {
        this.env.services.popup.close(this.quantity);
    }
}
