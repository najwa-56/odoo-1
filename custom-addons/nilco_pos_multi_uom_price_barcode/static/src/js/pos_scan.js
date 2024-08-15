/** @odoo-module */
import { unaccent } from "@web/core/utils/strings";
var DB = require('@point_of_sale/app/store/db');
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { Order, Orderline, Payment } from "@point_of_sale/app/store/models";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { ErrorBarcodePopup } from "@point_of_sale/app/barcode/error_popup/barcode_error_popup";
import { NumberBuffer } from '@point_of_sale/path_to_number_buffer'; // Adjust the path


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
        const currentOrder = this.env.pos.get_order();
        if (currentOrder.is_finalized) {
            this.showPopup('ErrorPopup', {
                title: 'Cannot Modify Finalized Order',
                body: 'The order has already been finalized and cannot be modified.',
            });
            return;
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
        if (!barcode) return undefined;

        const barcodes = Object.values(this.product_multi_barcodes);

        // Sort products based on their active status
        barcodes.sort((a, b) => {
            const aActive = a.active ? 1 : 0;
            const bActive = b.active ? 1 : 0;
            return bActive - aActive; // Descending order: active products come first
        });

        if (this.product_by_barcode[barcode]) {
            return this.product_by_barcode[barcode];
        } else if (this.product_packaging_by_barcode[barcode]) {
            return this.product_by_id[this.product_packaging_by_barcode[barcode].product_id[0]];
        } else if (barcodes.length > 0) {
            const productQuantities = {};

            for (const product of barcodes) {
                const uoms = Object.values(product.uom_id);
                for (const uom of uoms) {
                    if (uom.barcodes.includes(barcode)) {
                        const result = this.product_by_id[uom.product_variant_id[0]];

                        if (!productQuantities[result.id]) {
                            productQuantities[result.id] = {
                                product: result,
                                uom: uom,
                                quantity: 0
                            };
                        }

                        productQuantities[result.id].quantity += 1; // Aggregate quantities
                    }
                }
            }

            // Process aggregated products
            for (const productId in productQuantities) {
                const { product, uom, quantity } = productQuantities[productId];
                const currentOrder = product.pos.selectedOrder;

                if (currentOrder.is_finalized) {
                    this.showPopup('ErrorPopup', {
                        title: 'Cannot Modify Finalized Order',
                        body: 'The order has already been finalized and cannot be modified.',
                    });
                    return;
                }

                const line = new Orderline(
                    { env: product.env },
                    { pos: product.pos, order: currentOrder, product: product }
                );

                // Check if the product line already exists
                let existingLine = currentOrder.get_orderlines().find(line => line.product.id === product.id && line.product_uom_id[0] === uom.id);
                if (existingLine) {
                    existingLine.set_quantity(existingLine.quantity + quantity, uom.price);
                } else {
                    currentOrder.add_orderline(line);
                    currentOrder.selected_orderline.set_uom({ 0: uom.id, 1: uom.name });
                    currentOrder.selected_orderline.price_manually_set = true;
                    currentOrder.selected_orderline.set_unit_price(uom.price);
                    currentOrder.selected_orderline.set_quantity(quantity, uom.price);
                }
            }

            if (this.numberBuffer) {
                this.numberBuffer.reset();
            } else {
                console.error('numberBuffer is undefined');
            }

            return true;
        }
        return undefined;
    },
});
