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

    // async _downloadInvoice(orderId) {
    //     try {
    //         const [orderWithInvoice] = await this.orm.read(
    //             "pos.order",
    //             [orderId],
    //             ["account_move"],
    //             { load: false }
    //         );
    //         if (orderWithInvoice?.account_move) {
    //             if (orderWithInvoice.is_invoice_b2c) {
    //                 // Call B2C simplified tax invoice report
    //                 await this.report.doAction("othaim_zatca_integration.action_report_simplified_tax_invoice", [
    //                     orderWithInvoice.account_move,
    //                 ]);
    //             } else if (orderWithInvoice.is_invoice) {
    //                 // Call the standard tax invoice report
    //                 await this.report.doAction("othaim_zatca_integration.action_report_tax_invoice", [
    //                     orderWithInvoice.account_move,
    //                 ]);
    //             }
    //             else{
    //                 await this.report.doAction("othaim_zatca_integration.action_report_tax_invoice", [
    //                     orderWithInvoice.account_move,
    //                 ]);
    //             }
    //         }
    //     } catch (error) {
    //         if (error instanceof Error) {
    //             throw error;
    //         } else {
    //             // NOTE: error here is most probably undefined
    //             this.popup.add(ErrorPopup, {
    //                 title: _t("Network Error"),
    //                 body: _t("Unable to download invoice."),
    //             });
    //         }
    //     }
    // }


    async _downloadInvoice(orderId) {
        try {
            const [orderWithInvoice] = await this.orm.read(
                "pos.order",
                [orderId],
                ["account_move"],
                { load: false }
            );
    
            if (orderWithInvoice?.account_move) {
                const invoiceId = orderWithInvoice.account_move;
    
                // Browse account.move separately to get the invoice type and status
                const [invoice] = await this.orm.read(
                    "account.move",
                    [invoiceId],
                    ["l10n_sa_invoice_type", "l10n_sa_zatca_status"],
                    { load: false }
                );
    
                const invoiceType = invoice.l10n_sa_invoice_type;
                const zatcaStatus = invoice.l10n_sa_zatca_status;
    
    
                // First: if ZATCA status needs reporting or clearance
                if (zatcaStatus && (zatcaStatus.includes('not') || zatcaStatus.includes('error'))) {
                    if (invoiceType === 'Standard') {
                        // Standard Invoice -> send for clearance
                        await this.orm.call(
                            "account.move",
                            "send_for_clearance",
                            [invoiceId],
                            { context: this.env.session.user_context }
                        );
                    } else if (invoiceType === 'Simplified') {
                        // Simplified Invoice -> send for reporting
                        await this.orm.call(
                            "account.move",
                            "send_for_reporting",
                            [invoiceId],
                            { context: this.env.session.user_context }
                        );
                    }
                }
    
                // Second: after sending, download the invoice report
                if (orderWithInvoice.is_invoice_b2c) {
                    // invoiceType === 'Simplified'
                   
                    // B2C simplified tax invoice
                    await this.report.doAction(
                        "othaim_zatca_integration.action_report_simplified_tax_invoice",
                        [invoiceId]
                    );
                } else {
                    // B2B standard tax invoice
                    await this.report.doAction(
                        "othaim_zatca_integration.action_report_tax_invoice",
                        [invoiceId]
                    );
                }
            }
        } catch (error) {
            if (error instanceof Error) {
                throw error;
            } else {
                // Error case, show popup
                this.popup.add(ErrorPopup, {
                    title: _t("Network Error"),
                    body: _t("Unable to download invoice."),
                });
            }
        }
    }

    

  });