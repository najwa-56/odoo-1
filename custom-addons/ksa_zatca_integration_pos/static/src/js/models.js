/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.l10n_is_third_party_invoice = json.l10n_is_third_party_invoice;
        this.l10n_is_nominal_invoice = json.l10n_is_nominal_invoice;
        this.l10n_is_summary_invoice = json.l10n_is_summary_invoice;
        this.credit_debit_reason = json.credit_debit_reason;
    },
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.l10n_is_third_party_invoice = this.l10n_is_third_party_invoice ? 1 : 0;
        json.l10n_is_nominal_invoice = this.l10n_is_nominal_invoice ? 1 : 0;
        json.l10n_is_summary_invoice = this.l10n_is_summary_invoice ? 1 : 0;
        json.credit_debit_reason = this.credit_debit_reason;
        return json;
    },
});
