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

        console.log("get_product_by_barcode called with barcode:", barcode);

        const barcodes = Object.values(this.product_multi_barcodes);
        console.log("product_multi_barcodes:", barcodes);

        let product = null;
        if (this.product_by_barcode[barcode]) {
            product = this.product_by_barcode[barcode];
        } else if (this.product_packaging_by_barcode[barcode]) {
            product = this.product_by_id[this.product_packaging_by_barcode[barcode].product_id[0]];
        } else if (barcodes.length > 0) {
            product = this.find_product_by_barcode_in_barcodes(barcodes, barcode);
        }

        if (!product) {
            console.log("No product found for barcode:", barcode);
            return undefined;
        }

        console.log("Product found:", product);

        // Proceed with order line processing
        return this.process_order_line(product, barcode);
    },
    find_product_by_barcode_in_barcodes(barcodes, barcode) {
        for (const product of barcodes) {
            const uoms = Object.values(product.uom_id);
            for (const uom of uoms) {
                if (uom.barcodes.includes(barcode)) {
                    return this.product_by_id[uom.product_variant_id[0]];
                }
            }
        }
        return null;
    },
    process_order_line(product, barcode) {
        const result = product;
        const uoms = Object.values(product.uom_id);
        const orderlines = result.pos.selectedOrder.get_orderlines();

        for (const uom of uoms) {
            if (uom.barcodes.includes(barcode)) {
                console.log("Processing order line for uom:", uom);

                for (const orderline of orderlines) {
                    if (orderline.product.id === result.id &&
                        orderline.product_uom_id[0] === uom.id &&
                        orderline.price === uom.price) {

                        console.log("Existing order line found:", orderline);

                        // Update the quantity of the order line
                        orderline.set_quantity(orderline.quantity + 1, uom.price);

                        // Move the updated product to the end of the order lines
                        this.move_order_line_to_end(orderlines, orderline);

                        return true;
                    }
                }
                // If no existing order line, add a new one
                this.add_new_orderline(result, uom);
                return true;
            }
        }
        return undefined;
    },
    move_order_line_to_end(orderlines, orderline) {
        const index = orderlines.indexOf(orderline);
        if (index > -1) {
            orderlines.splice(index, 1); // Remove the existing order line
            orderlines.push(orderline); // Add it to the end
            console.log("Order line moved to end:", orderline);
        }
        // Re-select the moved order line to ensure UI consistency
        result.pos.selectedOrder.select_orderline(orderline);
    },
    add_new_orderline(result, uom) {
        const line = new Orderline(
            { env: result.env },
            { pos: result.pos, order: result.pos.selectedOrder, product: result }
        );
        result.pos.selectedOrder.add_orderline(line);
        result.pos.selectedOrder.selected_orderline.set_uom({ 0: uom.id, 1: uom.name });
        result.pos.selectedOrder.selected_orderline.price_manually_set = true;
        result.pos.selectedOrder.selected_orderline.set_unit_price(uom.price);
        console.log("New order line added:", line);
    }
});