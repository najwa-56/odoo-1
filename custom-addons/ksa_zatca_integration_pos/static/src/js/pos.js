import { PartnerDetailsEdit } from "@point_of_sale/app/screens/partner_list/partner_editor/partner_editor";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

console.log('PartnerDetailsEdit before patch:', PartnerDetailsEdit);

patch(PartnerDetailsEdit.prototype, 'custom-partner-details-edit', {
    setup() {
        console.log('PartnerDetailsEdit patch setup called');
        this._super.apply(this, arguments);  // Correctly call super
        const partner = this.props.partner;

        // Check if partner data is available
        console.log('Partner data:', partner);

        // Add new fields to changes state
        this.changes.building_no = partner.building_no || "";
        this.changes.additional_no = partner.additional_no || "";
        this.changes.district = partner.district || "";

        // Log changes for debugging
        console.log('Changes state after adding new fields:', this.changes);

        // Optionally, add translated terms for the new fields
        this.partnerDetailsFields = {
            ...this.partnerDetailsFields,
            'Building No': _t('Building No'),
            'Additional No': _t('Additional No'),
            'District': _t('District'),
        };

        console.log('Updated partnerDetailsFields:', this.partnerDetailsFields);
    },
});

console.log('PartnerDetailsEdit after patch:', PartnerDetailsEdit);
