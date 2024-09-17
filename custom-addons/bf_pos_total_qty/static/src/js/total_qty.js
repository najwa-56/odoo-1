/** @odoo-module */

import { OrderWidget } from "@point_of_sale/app/generic_components/order_widget/order_widget";
import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(OrderWidget, {
    props: {
        ...OrderWidget.props,
        qty: { type: String, optional: true },
    },
});

patch(Order.prototype, {
    setup(options) {
        super.setup(...arguments);
        this.total_quantity = this.total_quantity || 0;
    },
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.total_quantity = json.total_quantity || 0;
    },
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.total_quantity = this.total_quantity;
        return json;
    },
    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        result.total_quantity = this.get_total_quantity();
        return result;
    },
    get_total_quantity() {
        // acc: accumulator, line: current value
        this.total_quantity = this.orderlines.reduce((acc, line) => acc + line.quantity, 0);
        console.log('get_total_quantity', this.total_quantity);
        return this.total_quantity;
    },
});
