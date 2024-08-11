/** @odoo-module */
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { Component } from "@odoo/owl";
import { useListener } from "@web/core/utils/hooks";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";
import { _t } from "@web/core/l10n/translation";  // Import _t for translations

export class UOMButton extends Component {
    static template = "point_of_sale.UOMButton";
    setup() {
           super.setup();
       }
    get selectedOrderline() {
	       return this.env.services.pos.get_order().get_selected_orderline();
       }

    async onClick() {
        try {
            let line = this.selectedOrderline;
            console.log('Selected Order Line:', line);
            if (line) {
                let pupList = Object.keys(line.pos.product_uom_price || {});
                let product = line.product.product_tmpl_id;
                console.log('Product ID:', product);
                if (pupList.includes(product.toString())) {
                    const uomList = [];
                    let uomPrices = line.pos.product_uom_price[product]?.uom_id || {};
                    console.log('UOM Prices:', uomPrices);
                    Object.values(uomPrices).forEach(uomPrice => {
                        uomList.push({
                            id: uomPrice.id,
                            label: uomPrice.name_field || _t('No Name'), // Use 'name_field' instead of 'name'
                            isSelected: true,
                            item: uomPrice,
                        });
                    });
                    console.log('UOM List:', uomList);
                    const { confirmed, payload: selectedUOM } = await this.env.services.popup.add(
                        SelectionPopup, {
                            title: _t('UOM'),
                            list: uomList,
                        }
                    );
                    console.log('Popup Result:', confirmed, selectedUOM);
                    if (confirmed) {
                        line.set_uom({0: selectedUOM.id, 1: selectedUOM.name_field || _t('No Name')}); // Use 'name_field' instead of 'name'
                        line.price_manually_set = true;
                        line.set_unit_price(selectedUOM.price);
                    }
                }
            }
        } catch (error) {
            console.error('Error in onClick:', error);
        }
    }
}




ProductScreen.addControlButton({
    component: UOMButton,
    condition: function () {
        return true;
    },
});

