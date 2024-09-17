/** @odoo-module */
import { unaccent } from "@web/core/utils/strings";
var DB = require('@point_of_sale/app/store/db');
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { Order, Orderline, Payment } from "@point_of_sale/app/store/models";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { ErrorBarcodePopup } from "@point_of_sale/app/barcode/error_popup/barcode_error_popup";
let lastBarcodeTime = 0;
const debounceTime = 100;  // Adjust delay as needed

function handleBarcode(barcode, callback) {
    const currentTime = new Date().getTime();
    if (currentTime - lastBarcodeTime < debounceTime) {
        return;  // Ignore this barcode event if it comes too soon
    }
    lastBarcodeTime = currentTime;
    callback();  // Call the original barcode processing logic

}

patch(ProductScreen.prototype, {
    async _barcodeProductAction(code) {

        // Wrap barcode handling with debounce
        handleBarcode(code, async () => {
            const product = await this._getProductByBarcode(code);
            if (product === true) {
                return;
            }
            if (!product) {
                return this.popup.add(ErrorBarcodePopup, { code: code.base_code });
            }
            const options = await product.getAddProductOptions(code);
            if (!options) {
                return;
            }
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
        });
    },


});

patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.db.product_multi_barcodes = this.product_uom_price;
    }
});

patch(DB.PosDB.prototype, {
    init(options) {
        this._super.apply(this, arguments);
    },
    get_product_by_barcode(barcode) {
            if (!barcode) return undefined;

        const barcodes = Object.values(this.product_multi_barcodes);

        if (this.product_by_barcode[barcode]) {
            return this.product_by_barcode[barcode];
        } else if (this.product_packaging_by_barcode[barcode]) {
            return this.product_by_id[this.product_packaging_by_barcode[barcode].product_id[0]];
        } else if (barcodes.length > 0) {
            for (const product of barcodes) {
                const uoms = Object.values(product.uom_id);
                for (const uom of uoms) {
                    if (uom.barcodes.includes(barcode)) {
                        const result = this.product_by_id[uom.product_variant_id[0]];
                        const line = new Orderline(
                            { env: result.env },
                            { pos: result.pos, order: result.pos.selectedOrder, product: result }
                        );
                        const orderlines = result.pos.selectedOrder.get_orderlines();
                        for (const orderline of orderlines) {
                            if (orderline.product.id === result.id &&
                                orderline.product_uom_id[0] === uom.id &&
                                orderline.price === uom.price) {
                                const newQuantity = parseFloat(orderline.quantity) + 1;
                                orderline.set_quantity(newQuantity, uom.price);
                                orderline.set_uom_name(orderline.name_field );

                                  // Remove the orderline from its current position
                            result.pos.selectedOrder.orderlines.remove(orderline);

                            // Add it back to the end of the array
                            result.pos.selectedOrder.orderlines.push(orderline);
                              if (numberBuffer) {
                                    numberBuffer.reset();
                                }
                                return true;
                            }
                        }
                        result.pos.selectedOrder.add_orderline(line);
                        result.pos.selectedOrder.selected_orderline.set_uom({ 0: uom.id, 1: uom.name });
                        result.pos.selectedOrder.selected_orderline.price_manually_set = true;
                        result.pos.selectedOrder.selected_orderline.set_unit_price(uom.price);
                        result.pos.selectedOrder.selected_orderline.set_quantity(1,uom.price);
                         result.pos.selectedOrder.selected_orderline.set_uom_name(uom.name_field);
                           if (numberBuffer) {
                                    numberBuffer.reset();
                                }
                        return true;
                    }
                }
            }
            return undefined;
        }
        return undefined;
    },
});
