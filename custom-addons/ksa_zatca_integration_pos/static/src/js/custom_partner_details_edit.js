/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { Component, useState } from "@odoo/owl";
import { PartnerDetailsEdit as BasePartnerDetailsEdit } from "@point_of_sale/app/screens/partner_list/partner_editor/partner_editor";

export class CustomPartnerDetailsEdit extends BasePartnerDetailsEdit {
    setup() {
        super.setup(); // Call the base setup to inherit functionality

        const partner = this.props.partner;

        // Initialize changes with all partner fields
        this.changes = useState({
            name: partner.name || "",
            street: partner.street || "",
            city: partner.city || "",
            zip: partner.zip || "",
            state_id: partner.state_id && partner.state_id[0],
            country_id: partner.country_id && partner.country_id[0],
            lang: partner.lang || "",
            email: partner.email || "",
            phone: partner.phone || "",
            mobile: partner.mobile || "",
            barcode: partner.barcode || "",
            vat: partner.vat || "",
            property_product_pricelist: this.setDefaultPricelist(partner),
            // Add all other fields here, e.g., buyer_identification, buyer_identification_no
            buyer_identification: partner.buyer_identification || "",
            buyer_identification_no: partner.buyer_identification_no || "",
            // Add any additional fields as needed
             building_no: partner.building_no || "",  // Add building_no
            additional_no: partner.additional_no || "", // Add additional_no
            district: partner.district || "", // Add district
            country_id_name: partner.country_id_name || "", // Add country_id_name
        });

        // Provides translated terms used in the view
        this.partnerDetailsFields = {
            'Name': _t('Name'),
            'Street': _t('Street'),
            'City': _t('City'),
            'Zip': _t('Zip'),
            'Email': _t('Email'),
            'Phone': _t('Phone'),
            'Mobile': _t('Mobile'),
            'Barcode': _t('Barcode'),
            'VAT': _t('VAT'),
            // Add all other field translations
            'Buyer Identification': _t('Buyer Identification'),
            'Buyer Identification No': _t('Buyer Identification No'),
            // ... Add more fields here
        };
    }

    // Override saveChanges to handle all fields
    saveChanges() {
        const processedChanges = {};
        for (const [key, value] of Object.entries(this.changes)) {
            processedChanges[key] = value; // Directly assign value
        }
        processedChanges.id = this.props.partner.id || false;
        this.props.saveChanges(processedChanges);
    }
}
