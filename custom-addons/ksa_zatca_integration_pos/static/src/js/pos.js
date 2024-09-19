/** @odoo-module **/

import { PartnerDetailsEdit } from "@point_of_sale/app/screens/partner_list/partner_editor/partner_editor";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

// Apply the patch
patch(PartnerDetailsEdit.prototype, 'custom-partner-details-edit', {
    // Extending setup without recursion
    setup() {
        // Call the original setup first (in the correct way)
        super.setup(...arguments);  // this invokes the parent's setup correctly

        const partner = this.props.partner;

        // Add new fields to changes state
        this.changes.building_no = partner.building_no || "";
        this.changes.additional_no = partner.additional_no || "";
        this.changes.district = partner.district || "";

        // Optionally, add translated terms for the new fields
        this.partnerDetailsFields = {
            ...this.partnerDetailsFields,
            'Building No': _t('Building No'),
            'Additional No': _t('Additional No'),
            'District': _t('District'),
        };
    },
});
