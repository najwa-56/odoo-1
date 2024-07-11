/** @odoo-module **/

import { InvoiceButton } from "@point_of_sale/app/screens/invoice_button/invoice_button";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";

patch(InvoiceButton.prototype, {
    setup() {
        this._super(...arguments);

        this.orm = useService("orm");

    },
    async get_report(name) {
        let response = await this.orm.call('pos.order', 'get_simplified_zatca_report', [[], name]);
        if (response)
            response = $($(response)).find('.pos-receipt').parent().html();
        return response;
    },

    async tryReprint() {
        let report = await this.get_report(this.props.order.name)
        this.printer.printHtml($(report)[0], { webPrintFallback: true });
    }
  });