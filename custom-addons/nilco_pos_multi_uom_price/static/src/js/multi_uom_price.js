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
	       let line = this.selectedOrderline;
	       if (line) {
	         let pupList = Object.keys(line.pos.product_uom_price);
	         let product = line.product.product_tmpl_id;
	         if (line && pupList.find(element => element === product.toString())) {
		       const uomList = [ ];
		       let uomPrices = line.pos.product_uom_price[product].uom_id;
		       if (uomPrices) {
		       	Object.values(uomPrices).forEach(uomPrice => {
				       uomList.push({
					       id:	uomPrice.id,
					       label:	uomPrice.name,
					       isSelected: true,
					       item:	uomPrice,
				       });
				       });
		       }
		       const { confirmed, payload: selectedUOM } = await this.env.services.popup.add(
			            SelectionPopup, {
			       title: 'UOM',
			       list: uomList,
		       });
		       if (confirmed) {
                    let currentUOM = line.product.uom_id;
                    let newQuantity = line.quantity * (selectedUOM.ratio / currentUOM.ratio);

                    // Debugging: Check selectedUOM price
                    console.log('Selected UOM:', selectedUOM);
                    console.log('Selected UOM Price:', selectedUOM.price);

                    // Ensure price is not zero or undefined
                    if (selectedUOM.price !== undefined && selectedUOM.price > 0) {
                        line.set_uom({0: selectedUOM.id, 1: selectedUOM.name});
                        line.price_manually_set = true;
                        line.set_unit_price(selectedUOM.price);
                        line.set_quantity(newQuantity);  // Update the quantity based on the new UOM
                    } else {
                        console.error('Invalid price for selected UOM:', selectedUOM);
                        // Handle the error appropriately
                    }
                }
	         }
	       }
       }	   
   }


ProductScreen.addControlButton({
    component: UOMButton,
    condition: function () {
        return true;
    },
});

