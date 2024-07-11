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
  });