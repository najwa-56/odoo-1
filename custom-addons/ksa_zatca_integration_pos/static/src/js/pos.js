import { PartnerDetailsEdit } from "@point_of_sale/app/screens/partner_list/partner_editor/partner_editor";
import { patch } from "@web/core/utils/patch";

patch(PartnerDetailsEdit.prototype, {
    setup() {
        const res = super.setup(...arguments);
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
}

