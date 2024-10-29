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

    // async onClick() {
	//        let line = this.selectedOrderline;
	//        if (line) {
	//          let pupList = Object.keys(line.pos.product_uom_price);
	//          let product = line.product.product_tmpl_id;
	//          if (line && pupList.find(element => element === product.toString())) {
	// 	       const uomList = [ ];
	// 	       let uomPrices = line.pos.product_uom_price[product].uom_id;
	// 	     //  console.log(uomPrices);
	// 	       if (uomPrices) {
	// 	       	Object.values(uomPrices).forEach(uomPrice => {
	// 			       uomList.push({
	// 				       id:	uomPrice.id,
	// 				       label:	uomPrice.name_field,
	// 				       isSelected: true,
	// 				       item:	uomPrice,
	// 			       });
	// 			       });
	// 	       }
	// 	       const { confirmed, payload: selectedUOM } = await this.env.services.popup.add(
	// 		            SelectionPopup, {
	// 		       title: 'UOM',
	// 		       list: uomList,
	// 	       });
	// 	       if (confirmed) {
	// 		      line.set_product_uom(selectedUOM.id);
	// 			  line.set_uom({0:selectedUOM.id,1:selectedUOM.name});
	// 		      		   //    console.log(selectedUOM.id);
	// 		      line.price_manually_set = true;
	// 		      line.set_unit_price(selectedUOM.price);
	// 		      line.set_uom_name(selectedUOM.name_field);



	// 	       }
	//          }
	//        }
    //    }
	async onClick() {
		let line = this.selectedOrderline;
		if (line) {
		  let pupList = Object.keys(line.pos.product_uom_price);
		  let product = line.product.product_tmpl_id;
		  if (line && pupList.find(element => element === product.toString())) {
			const uomList = [ ];
			let uomPrices = line.pos.product_uom_price[product].barcodes;
		  //  console.log(uomPrices);
			// if (uomPrices) {
			//  Object.entries(uomPrices).forEach(([barcode, uomPrice]) => {
			// 	 let uniqueKey = `${uomPrice.uom_id[0]}_${barcode}`;
			// 		uomList.push({
			// 			id:	uniqueKey,
			// 			label:	uomPrice.name_field,
			// 			isSelected: true,
			// 			item:	uomPrice,
			// 			uom_id:	uomPrice.id,
			// 		});
			// 		});
			// }

			if (uomPrices) {
				const uniqueUoms = new Map();  // Map to store unique items based on `name_field` and `price`
			
				Object.entries(uomPrices).forEach(([barcode, uomPrice]) => {
					// Generate a unique key based on `name_field` and `price`
					const uniqueKey = `${uomPrice.name_field}_${uomPrice.price}`;
			
					// Only add to `uomList` if the combination of `name_field` and `price` is unique
					if (!uniqueUoms.has(uniqueKey)) {
						uniqueUoms.set(uniqueKey, true);  // Mark this unique combination as added
			
						uomList.push({
							id: `${uomPrice.uom_id[0]}_${barcode}`,
							label: uomPrice.name_field,
							isSelected: true,
							item: uomPrice,
							uom_id: uomPrice.id,
						});
					}
				});
			}
			const { confirmed, payload: selectedUOM } = await this.env.services.popup.add(
					 SelectionPopup, {
				title: 'UOM',
				list: uomList,
			});
			if (confirmed) {
			   line.set_product_uom(selectedUOM.id);
			   line.set_uom({0:selectedUOM.id,1:selectedUOM.name});
						  //    console.log(selectedUOM.id);
			   line.price_manually_set = true;
			   line.set_unit_price(selectedUOM.price);
			   line.set_uom_name(selectedUOM.name_field);



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

