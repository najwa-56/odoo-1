/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ClosePosPopup } from "@point_of_sale/app/navbar/closing_popup/closing_popup";

patch(ClosePosPopup.prototype, {
    //@Override
    getDifference(paymentId) {
        if (this.pos.config.hide_closing) {
            const expectedAmount =
                paymentId === this.props.default_cash_details?.id
                    ? this.props.default_cash_details.amount
                    : this.props.other_payment_methods.find((pm) => pm.id === paymentId).amount;

            this.state.payments[paymentId].counted = JSON.stringify(expectedAmount);
        }
        return super.getDifference(paymentId);
    },
})
