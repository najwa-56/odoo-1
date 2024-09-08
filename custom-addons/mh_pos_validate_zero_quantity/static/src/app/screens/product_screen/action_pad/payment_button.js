/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";

// Patch the Order model to override the pay() method
patch(Order.prototype, {
    async pay() {
        console.log('Patching Order model pay method');

        // Check if there are no order lines
        if (this.orderlines.length === 0) {
            // console.log("No products in the order. Cannot proceed with payment.");
            await this.env.services.popup.add(ConfirmPopup, {
                title: _t("Empty Order"),
                body: _t("There are no products in the order. Please add products to proceed."),
            });
            return;  // Stop further execution
        }

        // Check for order lines with zero quantity
        const zeroQuantityLines = this.orderlines.filter(line => line.quantity === 0);

        if (zeroQuantityLines.length > 0) {
            // Create a formatted list of products with zero quantity
            const productNames = zeroQuantityLines
                .map((line, index) => `${index + 1}. ${line.product.display_name}`)
                .join('\n');

            // console.log("Some products have a quantity of 0. Cannot proceed with payment.");
            await this.env.services.popup.add(ConfirmPopup, {
                title: _t("Invalid Quantities"),
                body: _t(`The following products have 0 quantity:\n${productNames}\n\n. Please correct the quantities to proceed.`),
            });
        } else {
            // Call the original pay() method if all is good
            return super.pay(...arguments);
            // await super.setup();
        }
    },
});

