/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { ConnectionLostError } from "@web/core/network/rpc_service";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";


patch(PaymentScreen.prototype, {
   
    shouldDownloadInvoice() {
        if (this.currentOrder.is_invoice_b2b || this.currentOrder.is_invoice_b2c) {
            return true
        }
        
        return false
    },
   

  
    
    Refund_Reason() {
        // this.currentOrder.credit_debit_reason = arguments[0].currentTarget.value;
        this.currentOrder.credit_debit_reason = 'مرتجع العميل';
    },
    

    toggleIsInvoiceB2b() {
        this.currentOrder.set_to_invoice_b2b(true);
        this.currentOrder.set_to_invoice_b2c(false);

        this.currentOrder.set_no_invoice(false);
        this.currentOrder.set_to_invoice(true);
       
    },
    
    toggleIsInvoiceB2c() {
        this.currentOrder.set_to_invoice_b2c(true);
        this.currentOrder.set_to_invoice_b2b(false);

        this.currentOrder.set_no_invoice(false);
        this.currentOrder.set_to_invoice(true);
        
    },

    toggleNoInvoice() {
        this.currentOrder.set_no_invoice(true);

        this.currentOrder.set_to_invoice_b2b(false);
        this.currentOrder.set_to_invoice_b2c(false);
        this.currentOrder.set_to_invoice(false);
    },
    

    
    
    
  

 


   
    async _finalizeValidation() {
        if (this.currentOrder.is_paid_with_cash() || this.currentOrder.get_change()) {
            this.hardwareProxy.openCashbox();
        }
        this.currentOrder.date_order = luxon.DateTime.now();
        for (const line of this.paymentLines) {
            if (!line.amount === 0) {
                this.currentOrder.remove_paymentline(line);
            }
        }
        this.currentOrder.finalized = true;

        this.env.services.ui.block();
        let syncOrderResult;
        try {
            // 1. Save order to server.
            syncOrderResult = await this.pos.push_single_order(this.currentOrder);
            if (!syncOrderResult) {
                return;
            }
            // 2. Invoice.
            if (this.shouldDownloadInvoice() && this.currentOrder.is_to_invoice()) {
                if (syncOrderResult[0]?.account_move) {

                    if (this.currentOrder.is_invoice_b2c) {
                        // Call B2C simplified tax invoice report
                        await this.report.doAction("othaim_zatca_integration.action_report_simplified_tax_invoice", [
                            syncOrderResult[0].account_move,
                        ]);
                    } else if (this.currentOrder.is_invoice_b2b) {
                        // Call the standard tax invoice report
                        await this.report.doAction("othaim_zatca_integration.action_report_tax_invoice", [
                            syncOrderResult[0].account_move,
                        ]);
                    }

                   
                } else {
                    throw {
                        code: 401,
                        message: "Backend Invoice",
                        data: { order: this.currentOrder },
                    };
                }
            }
        } catch (error) {
            if (error instanceof ConnectionLostError) {
                this.pos.showScreen(this.nextScreen);
                Promise.reject(error);
                return error;
            } else {
                throw error;
            }
        } finally {
            this.env.services.ui.unblock();
        }

        // 3. Post process.
        if (
            syncOrderResult &&
            syncOrderResult.length > 0 &&
            this.currentOrder.wait_for_push_order()
        ) {
            await this.postPushOrderResolve(syncOrderResult.map((res) => res.id));
        }

        await this.afterOrderValidation(!!syncOrderResult && syncOrderResult.length > 0);
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

        const is_b2b_or_b2c = this.currentOrder.is_to_b2b_invoice?.() || this.currentOrder.is_to_b2c_invoice?.();
        print("is_b2b_or_b2c=====================",is_b2b_or_b2c)
        if (
            nextScreen === "ReceiptScreen" &&
            !this.currentOrder._printed &&
            this.pos.config.iface_print_auto &&
            !is_b2b_or_b2c
        ) {
            const invoiced_finalized = this.currentOrder.is_to_invoice()
                ? this.currentOrder.finalized
                : true;

            if (invoiced_finalized) {
                const printResult = await this.printer.print(
                    OrderReceipt,
                    {
                        data: this.pos.get_order().export_for_printing(),
                        formatCurrency: this.env.utils.formatCurrency,
                    },
                    { webPrintFallback: true }
                );

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
