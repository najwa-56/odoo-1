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
                    // Access UOM and ratio directly from the line's properties
                    const previousUOMId = line.uom_id; // Accessing UOM ID directly if available
                    const quantity = line.quantity; // Assuming `quantity` is a property of line
                    const previousUOMRatio = previousUOMId ? line.pos.product_uom_price[product].uom_id[previousUOMId].ratio : 1;
                    const selectedUOMRatio = selectedUOM.ratio;

                    // Adjust the quantity based on the ratio of the UOMs
                    const newQuantity = (quantity * previousUOMRatio) / selectedUOMRatio;

                    line.set_uom({0: selectedUOM.id, 1: selectedUOM.name});
                    line.price_manually_set = true;
                    line.set_unit_price(selectedUOM.price);
                    line.set_quantity(newQuantity); // Update quantity based on UOM
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

