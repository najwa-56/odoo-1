/** @odoo-module */
import { _t } from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";

patch(PaymentScreen.prototype, {
    //false to not print and dowonload the invoice as no need it can be printed in backend by accountant
    //change to true if you want to pirnt and downalod the invoice in pos session
    shouldDownloadInvoice() {
        if (this.pos.config.print_invoice) {
            return true
        }
        return false
    },
    
});
