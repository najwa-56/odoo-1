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
      // Inherit and extend the _product_search_string method
    _product_search_string(product) {
        // First, replicate the original logic (without _super)
        let str = product.display_name;
        if (product.barcode) {
            str += "|" + product.barcode;
        }
        if (product.default_code) {
            str += "|" + product.default_code;
        }
        if (product.description) {
            str += "|" + product.description;
        }
        if (product.description_sale) {
            str += "|" + product.description_sale;
        }

        // Add custom multi-barcode handling logic
        if (product.multi_barcodes && product.multi_barcodes.length) {
            product.multi_barcodes.forEach((barcode) => {
                str += "|" + barcode;
            });
        }

        // Format the string
        str = product.id + ":" + str.replace(/[\n:]/g, "") + "\n";
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
                if (orderline.product.id === product.id ) {
                    const newQuantity = parseFloat(orderline.quantity) + 1;
                    orderline.set_quantity(newQuantity, product.lst_price);
                    orderline.set_uom_name(orderline.name_field);

                    // Move the orderline to the end of the orderlines array
                    product.pos.selectedOrder.orderlines.remove(orderline);
                    product.pos.selectedOrder.orderlines.push(orderline);

                    return true;
                }
            }

            // If no matching orderline is found, create a new orderline
            const line = new Orderline(
                { env: product.env },
                { pos: product.pos, order: product.pos.selectedOrder, product: product }
            );
            product.pos.selectedOrder.add_orderline(line);
            return true;
        } else if (this.product_packaging_by_barcode[barcode]) {
            return this.product_by_id[this.product_packaging_by_barcode[barcode].product_id[0]];
        } else if (barcodes.length > 0) {
            for (const product of barcodes) {
                const uoms = Object.values(product.uom_id);
                for (const uom of uoms) {
                    // Check if the UOM barcode matches
                    if (uom.barcodes.includes(barcode)) {
                        const result = this.product_by_id[uom.product_variant_id[0]];
                        const orderlines = result.pos.selectedOrder.get_orderlines();

                        for (const orderline of orderlines) {
                            // Apply the condition to UOM barcode
                            if (orderline.product.id === result.id &&
                                orderline.product_uom_id[0] === uom.id &&
                                orderline.price === uom.price) {
                                const newQuantity = parseFloat(orderline.quantity) + 1;
                                orderline.set_quantity(newQuantity, uom.price);
                                orderline.set_uom_name(orderline.name_field);

                                // Move the orderline to the end of the orderlines array
                                result.pos.selectedOrder.orderlines.remove(orderline);
                                result.pos.selectedOrder.orderlines.push(orderline);

                                return true;
                            }
                        }

                        // If no matching orderline is found, create a new orderline with UOM
                        const line = new Orderline(
                            { env: result.env },
                            { pos: result.pos, order: result.pos.selectedOrder, product: result }
                        );
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
