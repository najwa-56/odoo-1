/** @odoo-module */
import { unaccent } from "@web/core/utils/strings";
var DB = require('@point_of_sale/app/store/db');
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { Order, Orderline, Payment } from "@point_of_sale/app/store/models";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { ErrorBarcodePopup } from "@point_of_sale/app/barcode/error_popup/barcode_error_popup";

patch(ProductScreen.prototype, {
 setup() {
        super.setup();  // Correct usage of super instead of this._super()
        this.isErrorActive = false; // Initialize the error flag
    },
    async _barcodeProductAction(code) {
    if (this.isErrorActive) {
            return;
        }
        const handleBarcodeRetry = async (code) => {
            // Attempt to get the product by barcode
            const product = await this._getProductByBarcode(code);
            if (product === true) {
                return;  // Product found and successfully processed
            }

            // If product is not found, show the error popup
            if (!product) {
                this.isErrorActive = true;  // Set error active to block further scans
                return this.showPopup('ErrorBarcodePopup', {
                    code: code.base_code,
                    confirm: async () => {
                        this.isErrorActive = false;  // Reset flag when OK is pressed
                        await handleBarcodeRetry(code);  // Retry scanning the barcode
                    },
                });
            }}
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
    }
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
                                orderline.set_quantity(orderline.quantity + 1, uom.price);
                                  orderline.set_uom_name(orderline.name_field );
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
