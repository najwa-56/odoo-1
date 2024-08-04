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
                // Set the new UOM
                line.set_uom({0: selectedUOM.id, 1: selectedUOM.name});
                line.price_manually_set = true;

                // Calculate and set the new price based on UOM
                const newPrice = selectedUOM.price * (line.get_quantity() || 1); // Adjust the formula based on your pricing rules
                line.set_unit_price(newPrice);

                // Optionally update the quantity if required
                // line.set_quantity(newQuantity); // Set a new quantity if needed
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

