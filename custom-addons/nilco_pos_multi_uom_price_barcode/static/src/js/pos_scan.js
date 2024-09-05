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
            return;
        }
        if (!product) {
            return this.showPopup('ErrorBarcodePopup', { code: code.base_code });
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
            // If dealing with weight, calculate the price based on the weight.
            if (code.type === "weight") {
                const uom = this.env.pos.db.getUOMByBarcode(code.barcode); // Fetch the UOM linked to this barcode.
                const unitPrice = uom.price; // Price per UOM unit.
                const weight = code.value; // Weight value scanned from the barcode.
                const calculatedPrice = unitPrice * weight; // Calculate total price based on weight.

                Object.assign(options, {
                    price: calculatedPrice,
                    quantity: weight, // Treat weight as quantity in this context.
                    merge: false,
                });
            } else {
                // If it's quantity without weight, just use the value as is.
                Object.assign(options, {
                    quantity: code.value,
                    merge: false,
                });
            }
        } else if (code.type === "discount") {
            Object.assign(options, {
                discount: code.value,
                merge: false,
            });
        }
        const currentOrder = this.env.pos.get_order();
        if (currentOrder.is_finalized) {
            this.showPopup('ErrorPopup', {
                title: 'Cannot Modify Finalized Order',
                body: 'The order has already been finalized and cannot be modified.',
            });
            return;
        }
        currentOrder.add_product(product, options);
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

                        // Determine price based on whether the barcode is weight-based
                        let calculatedPrice;
                        if (barcode.type === 'weight') {
                            const weight = barcode.value; // Weight value from the barcode.
                            calculatedPrice = uom.price * weight; // Calculate price based on weight.
                        } else {
                            calculatedPrice = uom.price; // Use standard UOM price if not weight-based.
                        }

                        // Update or create the order line with the calculated price
                        const orderlines = result.pos.selectedOrder.get_orderlines();
                        for (const orderline of orderlines) {
                            if (orderline.product.id === result.id &&
                                orderline.product_uom_id[0] === uom.id &&
                                orderline.price === calculatedPrice) {
                                orderline.set_quantity(orderline.quantity + 1, calculatedPrice);
                                orderline.set_uom_name(uom.name_field);
                                return true;
                            }
                        }

                        // If no matching order line found, create a new one
                        result.pos.selectedOrder.add_orderline(line);
                        result.pos.selectedOrder.selected_orderline.set_uom({ 0: uom.id, 1: uom.name });
                        result.pos.selectedOrder.selected_orderline.price_manually_set = true;
                        result.pos.selectedOrder.selected_orderline.set_unit_price(calculatedPrice);
                        result.pos.selectedOrder.selected_orderline.set_uom_name(uom.name_field);
                        return true;
                    }
                }
            }
        }
        return undefined;
    },
});
