/** @odoo-module */


import {patch} from "@web/core/utils/patch";
import {PartnerDetailsEdit} from "@point_of_sale/app/screens/partner_list/partner_editor/partner_editor";

patch(PartnerDetailsEdit.prototype, {
    setup() {
        super.setup()
        const partner = this.props.partner;
        this.changes.buyer_identification_no = partner.buyer_identification_no || '';
        this.changes.building_no = partner.building_no || "";
        this.changes.additional_no = partner.additional_no || "";
        this.changes.district = partner.district || "";

        // Provides translated terms used in the view
        this.partnerDetailsFields = {
            'buyer_identification_no': _t('buyer_identification_no'),
            'building_no': _t('building_no'),
            'Zip': _t('Zip'),
            'additional_no': _t('additional_no'),
            'district': _t('district'),
        };
    },
    

    async saveChanges() {
        if (
            (!this.props.partner.buyer_identification_no && !this.changes.buyer_identification_no) ||
            this.changes.buyer_identification_no === ""
        ) {
            this.changes.buyer_identification_no = ""
        }
        if (
            (!this.props.partner.district && !this.changes.district) ||
            this.changes.district === ""
        ) {
            this.changes.district = ""
        }
        if (
            (!this.props.partner.additional_no && !this.changes.additional_no) ||
            this.changes.additional_no === ""
        ) {
            this.changes.additional_no = ""
        }
        if (
            (!this.props.partner.building_no && !this.changes.building_no) ||
            this.changes.building_no === ""
        ) {
            this.changes.building_no = ""
        }

        

        await super.saveChanges();
    },
})


