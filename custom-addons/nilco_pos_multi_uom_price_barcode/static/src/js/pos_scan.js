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
      this.numberBuffer.reset();
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
     _product_search_string(product) {
        // Start with the default product name and reference
        let str = product.display_name;
        if (product.reference) {
            str += '|' + product.reference;
        }

        // 1. Include the original product barcode in the search string
        if (product.barcode) {
            str += '|' + product.barcode;
        }

        // 2. Add multi-UOM barcodes to the search string
        if (product.uom_id && product.uom_id.length > 0) {
            for (const uom of product.uom_id) {
                if (uom.barcodes && uom.barcodes.length > 0) {
                    for (const uom_barcode of uom.barcodes) {
                        str += '|' + uom_barcode;
                    }
                }
            }
        }

        // 3. Return the search string with all barcodes (original and UOM)
        return str;
    },
    get_product_by_barcode(barcode) {
            if (!barcode) return undefined;

        const barcodes = Object.values(this.product_multi_barcodes);

                if (this.product_by_barcode[barcode]) {
            const product = this.product_by_barcode[barcode];
            const orderlines = product.pos.selectedOrder.get_orderlines();

            for (const orderline of orderlines) {
                // Check if the orderline matches the original product barcode
                if (orderline.product.id === product.id) {
                    let newQuantity;
                    if (orderline.price === product.lst_price) {
                        // Handle weight or quantity barcode types
                        if (barcode.type === "weight") {
                            // Assume the barcode.value represents the weight
                            newQuantity = parseFloat(orderline.quantity) + parseFloat(barcode.value);
                        } else if (barcode.type === "quantity") {
                            // Assume the barcode.value represents the quantity
                            newQuantity = parseFloat(orderline.quantity) + parseFloat(barcode.value);
                        } else {
                            // Handle other types as before
                            newQuantity = parseFloat(orderline.quantity) + 1;
                        }

                        // Update the quantity and position of the orderline
                        orderline.set_quantity(newQuantity, product.lst_price);
                        product.pos.selectedOrder.orderlines.remove(orderline);
                        product.pos.selectedOrder.orderlines.push(orderline);

                        return true;
                    }
                }
            }
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


                                return true;
                            }
                        }
                        result.pos.selectedOrder.add_orderline(line);
                        result.pos.selectedOrder.selected_orderline.set_uom({ 0: uom.id, 1: uom.name });
                        result.pos.selectedOrder.selected_orderline.price_manually_set = true;
                        result.pos.selectedOrder.selected_orderline.set_unit_price(uom.price);
                         result.pos.selectedOrder.selected_orderline.set_uom_name(uom.name_field);
                        return true;
                    }
                }
            }
            return undefined;
        }
        return undefined;
    },
});
