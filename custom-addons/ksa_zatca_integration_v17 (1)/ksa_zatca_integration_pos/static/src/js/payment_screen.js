/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        if (!this.currentOrder.is_to_invoice())
            this.toggleIsToInvoice();
    },
    async _isOrderValid(isForceValidate) {
        const res = super._isOrderValid(...arguments);
        if (res)
            if (this.currentOrder.get_total_with_tax() < 0 && _.contains([undefined, false, NaN, ''], this.currentOrder.credit_debit_reason)) {
                this.popup.add(ErrorPopup, {
                    title: _t("Zatca Validation Error"),
                    body: _t(
                        "Reason is compulsory for returns for zatca."
                    ),
                });
                return false;
            }
            else if (!this.currentOrder.is_to_invoice()){
                this.popup.add(ErrorPopup, {
                    title: _t("Zatca Validation Error"),
                    body: _t(
                        "Invoice is compulsory for zatca."
                    ),
                });
                return false;
            }
        return res
    },
    toggleIsThirdParty() {
        this.currentOrder.l10n_is_third_party_invoice = this.currentOrder.l10n_is_third_party_invoice ? 0 : 1;
    },
    toggleIsNominal() {
        this.currentOrder.l10n_is_nominal_invoice = this.currentOrder.l10n_is_nominal_invoice ? 0 : 1;
    },
    toggleIsSummary() {
        this.currentOrder.l10n_is_summary_invoice = this.currentOrder.l10n_is_summary_invoice ? 0 : 1;
    },
    Refund_Reason() {
        this.currentOrder.credit_debit_reason = arguments[0].currentTarget.value;
    },
    async get_report(name) {
        let response = await this.orm.call('pos.order', 'get_simplified_zatca_report', [[], name]);
        if (response)
            response = $($(response)).find('.pos-receipt').parent().html()
        return response
    },
    async afterOrderValidation(suggestToSync = true) {
        // Remove the order from the local storage so that when we refresh the page, the order
        // won't be there
        this.pos.db.remove_unpaid_order(this.currentOrder);

        // Ask the user to sync the remaining unsynced orders.
        if (suggestToSync && this.pos.db.get_orders().length) {
            const { confirmed } = await this.popup.add(ConfirmPopup, {
                title: _t("Remaining unsynced orders"),
                body: _t("There are unsynced orders. Do you want to sync these orders?"),
            });
            if (confirmed) {
                // NOTE: Not yet sure if this should be awaited or not.
                // If awaited, some operations like changing screen
                // might not work.
                this.pos.push_orders();
            }
        }
        // Always show the next screen regardless of error since pos has to
        // continue working even offline.
        let nextScreen = this.nextScreen;

        if (
            nextScreen === "ReceiptScreen" &&
            !this.currentOrder._printed &&
            this.pos.config.iface_print_auto
        ) {
            const invoiced_finalized = this.currentOrder.is_to_invoice()
                ? this.currentOrder.finalized
                : true;

            if (this.hardwareProxy.printer && invoiced_finalized) {
                let report = await this.get_report(this.props.order.name)
                const printResult = await this.printer.printHtml($(report)[0], { webPrintFallback: true });
                if (printResult && this.pos.config.iface_print_skip_screen) {
                    this.pos.removeOrder(this.currentOrder);
                    this.pos.add_new_order();
                    nextScreen = "ProductScreen";
                }
            }
        }

        this.pos.showScreen(nextScreen);
    }

});
