/** @odoo-module */
import { unaccent } from "@web/core/utils/strings";
var DB = require('@point_of_sale/app/store/db');
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { Order, Orderline, Payment } from "@point_of_sale/app/store/models";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { ErrorBarcodePopup } from "@point_of_sale/app/barcode/error_popup/barcode_error_popup";
patch(ProductScreen.prototype, {
     async _barcodeProductAction(code) {
        const product = await this._getProductByBarcode(code);
        if (product === true) {
            return ;
        }
        if (!product) {
            return this.popup.add(ErrorBarcodePopup, { code: code.base_code });
        }
        const options = await product.getAddProductOptions(code);
        // Do not proceed on adding the product when no options is returned.
        // This is consistent with clickProduct.
        if (!options) {
            return;
        }

        // update the options depending on the type of the scanned code
        if (code.type === "price") {
            Object.assign(options, {
                price: code.value,
                extras: {
                    price_type: "manual",
                },
            });
        } else if (code.type === "weight" || code.type === "quantity") {
            Object.assign(options, {
                quantity: code.value,
                merge: false,
            });
        } else if (code.type === "discount") {
            Object.assign(options, {
                discount: code.value,
                merge: false,
            });
        }
        this.currentOrder.add_product(product, options);
        this.numberBuffer.reset();

    }
});
patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(...arguments);
            // this.product_multi_barcodes = loadedData['multi.barcode.products'];
            this.db.product_multi_barcodes=this.product_uom_price;
    }
});
patch(DB.PosDB.prototype, { 
     init(options){
        this._super.apply(this, arguments);
    },
    get_product_by_barcode(barcode){
        var barcodes = Object.values(this.product_multi_barcodes);
        if(this.product_by_barcode[barcode]){
            return this.product_by_barcode[barcode];
        } else if (this.product_packaging_by_barcode[barcode]) {
            return this.product_by_id[this.product_packaging_by_barcode[barcode].product_id[0]];
            }else if (barcodes.length > 0) {

            for(var t=0;t < barcodes.length;t++){
                 var uoms=Object.values(barcodes[t].uom_id);
                    for(var b=0;b < uoms.length;b++){
                        if (uoms[b].barcode == barcode){
                            var result = this.product_by_id[uoms[b].product_variant_id[0]];

                            const line = new Orderline(
                                    { env: result.env },
                                    { pos: result.pos, order: result.pos.selectedOrder, product: result}
                                );
                            for (var i = 0; i < result.pos.selectedOrder.orderlines.length; i++) {
                                if (result.pos.selectedOrder.orderlines.at(i).product.id === result.id && 
                                result.pos.selectedOrder.orderlines.at(i).product_uom_id[0] === uoms[b].id &&
                                result.pos.selectedOrder.orderlines.at(i).price === uoms[b].price) {
                                 result.pos.selectedOrder.orderlines.at(i).set_quantity(result.pos.selectedOrder.orderlines.at(i).quantity+1,uoms[b].price);
                                 return true
                                }
                               
                            }
                            result.pos.selectedOrder.add_orderline(line);
                            result.pos.selectedOrder.selected_orderline.set_uom({0:uoms[b].id,1:uoms[b].name});
                            result.pos.selectedOrder.selected_orderline.price_manually_set = true;
                            result.pos.selectedOrder.selected_orderline.set_unit_price(uoms[b].price);
                             return true
                          
                        }
                    }
            }
            return undefined;    
        }
        return undefined;
    },
    
});
