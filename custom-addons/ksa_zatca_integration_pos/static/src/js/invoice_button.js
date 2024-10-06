/** @odoo-module **/

import { InvoiceButton } from "@point_of_sale/app/screens/ticket_screen/invoice_button/invoice_button";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";

patch(InvoiceButton.prototype, {
     setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
    },
    async get_report(name) {
        let response = await this.orm.call('pos.order', 'get_simplified_zatca_report', [[], name]);
        if (response)
            response = $($(response)).find('.pos-receipt').parent().html();
        return response;
    },

    // async tryReprint() {
    //     let report = await this.get_report(this.props.order.name)
    //     this.printer.printHtml($(report)[0], { webPrintFallback: true });
    // },

    async _downloadInvoice(orderId) {
        try {
            const [orderWithInvoice] = await this.orm.read(
                "pos.order",
                [orderId],
                ["account_move"],
                { load: false }
            );
            if (orderWithInvoice?.account_move) {
                if (orderWithInvoice.is_invoice_b2c) {
                    // Call B2C simplified tax invoice report
                    await this.report.doAction("ksa_zatca_integration.action_report_simplified_tax_invoice", [
                        orderWithInvoice.account_move,
                    ]);
                } else if (orderWithInvoice.is_invoice) {
                    // Call the standard tax invoice report
                    await this.report.doAction("ksa_zatca_integration.action_report_tax_invoice", [
                        orderWithInvoice.account_move,
                    ]);
                }
                else{
                    await this.report.doAction("ksa_zatca_integration.action_report_tax_invoice", [
                        orderWithInvoice.account_move,
                    ]);
                }
            }
        } catch (error) {
            if (error instanceof Error) {
                throw error;
            } else {
                // NOTE: error here is most probably undefined
                this.popup.add(ErrorPopup, {
                    title: _t("Network Error"),
                    body: _t("Unable to download invoice."),
                });
            }
        }
    }
  });