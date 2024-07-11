/** @odoo-module **/

import { InvoiceButton } from "@point_of_sale/app/components/invoice_button/invoice_button";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useRef } from "@odoo/owl";

patch(InvoiceButton.prototype, {
    setup() {
        this._super(...arguments);
        this.pos = usePos();
        this.invoiceButton = useRef("invoice-button");
        this.popup = useService("popup");
        this.orm = useService("orm");
        this.report = useService("report");
    },
    async get_report(name) {
        let response = await this.orm.call('pos.order', 'get_simplified_zatca_report', [[], name]);
        if (response)
            response = $($(response)).find('.pos-receipt').parent().html();
        return response;
    },
    async _downloadInvoice(orderId) {
        try {
            const [orderWithInvoice] = await this.orm.read(
                "pos.order",
                [orderId],
                ["account_move"],
                { load: false }
            );
            if (orderWithInvoice?.account_move) {
                let report = await this.get_report(orderWithInvoice.account_move);
                if (report) {
                    this.report.printHtml($(report)[0], { webPrintFallback: true });
                }
            }
        } catch (error) {
            if (error instanceof Error) {
                throw error;
            } else {
                this.popup.add(ErrorPopup, {
                    title: _t("Network Error"),
                    body: _t("Unable to download invoice."),
                });
            }
        }
    },
    async onWillInvoiceOrder(order) {
        return true;
    },
    async _invoiceOrder() {
        const order = this.props.order;
        if (!order) {
            return;
        }

        const orderId = order.backendId;

        if (this.isAlreadyInvoiced) {
            await this._downloadInvoice(orderId);
            return;
        }

        const prevPartner = order.get_partner();
        if (!prevPartner) {
            const { confirmed: confirmedPopup } = await this.popup.add(ConfirmPopup, {
                title: _t("Need customer to invoice"),
                body: _t("Do you want to open the customer list to select customer?"),
            });
            if (!confirmedPopup) {
                return;
            }

            const { confirmed: confirmedTempScreen, payload: newPartner } =
                await this.pos.showTempScreen("PartnerListScreen");
            if (!confirmedTempScreen) {
                return;
            }

            await this.orm.write("pos.order", [orderId], { partner_id: newPartner.id });
            order.set_partner(newPartner);
        }

        const confirmed = await this.onWillInvoiceOrder(order);
        if (!confirmed) {
            order.set_partner(prevPartner);
            return;
        }

        await this.orm.silent.call("pos.order", "action_pos_order_invoice", [orderId]);

        await this._downloadInvoice(orderId);
        this.props.onInvoiceOrder(orderId);
    },
    async click() {
        try {
            this.invoiceButton.el.style.pointerEvents = "none";
            await this._invoiceOrder();
        } finally {
            this.invoiceButton.el.style.pointerEvents = "auto";
        }
    }
});
