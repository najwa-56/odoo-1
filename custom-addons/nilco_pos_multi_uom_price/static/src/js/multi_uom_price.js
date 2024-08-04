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
           this.product_uom_id = this.product_uom_id || this.product.uom_id;
        this.on('change:quantity', this._onQuantityChange.bind(this));
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
			      line.set_uom({0:selectedUOM.id,1:selectedUOM.name});
			      line.price_manually_set = true;
			      line.set_unit_price(selectedUOM.price);
		       }
	         }
	       }
       }
       _onQuantityChange() {
        let line = this.selectedOrderline;
        if (line) {
            // Assuming the price should be updated based on the current UOM
            let uom = line.get_unit();
            if (uom) {
                let price = uom.price;
                line.set_unit_price(price);
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

