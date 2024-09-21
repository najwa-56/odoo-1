/** @odoo-module */
import { unaccent } from "@web/core/utils/strings";
var DB = require('@point_of_sale/app/store/db');
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { Order, Orderline, Payment } from "@point_of_sale/app/store/models";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { ErrorBarcodePopup } from "@point_of_sale/app/barcode/error_popup/barcode_error_popup";

let lastBarcodeTime = 0;
const debounceTime = 50;  // Adjust delay as needed
let orderlineBuffer = [];  // Buffer for batch processing
let batchTimer = null;
const batchProcessingInterval = 3000;  // Process batch every 3 seconds

// Function to add product and options to buffer
function addToOrderlineBuffer(product, options) {
    // Check if the product already exists in the buffer
    const existingEntry = orderlineBuffer.find(entry => entry.product.id === product.id);

    if (existingEntry) {
        // If the product exists, accumulate the quantity
        existingEntry.quantity += options.quantity;
    } else {
        // Add new product entry to the buffer
        orderlineBuffer.push({
            product: product,
            quantity: options.quantity,
            options: options,
        });
    }

    // Start the batch timer if it's not already running
    if (!batchTimer) {
        startBatchProcessing();
    }
}

// Function to start the batch processing timer
function startBatchProcessing() {
    batchTimer = setTimeout(() => {
        processOrderlineBuffer();
    }, batchProcessingInterval);
}

// Function to process and update orderlines in bulk
function processOrderlineBuffer() {
    if (orderlineBuffer.length === 0) {
        // No items to process, stop the timer
        clearTimeout(batchTimer);
        batchTimer = null;
        return;
    }

    const currentOrder = this.currentOrder;

    // Process each entry in the buffer
    for (const entry of orderlineBuffer) {
        const product = entry.product;
        const options = entry.options;

        // Find if the orderline for this product already exists
        const orderline = currentOrder.get_orderlines().find(line => line.product.id === product.id);

        if (orderline) {
            // Update the quantity of the existing orderline
            const newQuantity = orderline.quantity + entry.quantity;
            orderline.set_quantity(newQuantity, orderline.price);
        } else {
            // Add a new orderline for this product
            currentOrder.add_product(product, options);
        }
    }

    // Clear the buffer after processing
    orderlineBuffer = [];

    // Restart the timer for the next batch
    startBatchProcessing();
}

// Function to force immediate processing of the buffer (e.g., before order submission)
function forceProcessBuffer() {
    if (batchTimer) {
        processOrderlineBuffer();  // Process the buffer immediately
        clearTimeout(batchTimer);  // Clear the timer
        batchTimer = null;
    }
}

// Barcode handler with debounce logic
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
        this.initialQuantities = {}; // Initialize initial quantities object
    },

    get_product_by_barcode(barcode) {
            if (!barcode) return undefined;

        const barcodes = Object.values(this.product_multi_barcodes);

        if (this.product_by_barcode[barcode]) {
    const product = this.product_by_barcode[barcode];
    const orderlines = product.pos.selectedOrder.get_orderlines();

    for (const orderline of orderlines) {
        // Check if the orderline matches the original product barcode
                if (orderline.product.id === product.id && orderline.price === product.lst_price) {
                    const key = `${product.id}-${product.lst_price}`; // Unique key for tracking initial quantity

                    // Ensure initialQuantities is initialized
                    if (typeof this.initialQuantities === 'undefined') {
                        this.initialQuantities = {};
                    }

                    if (!(key in this.initialQuantities)) {
                        // Store the initial quantity only the first time
                        this.initialQuantities[key] = parseFloat(orderline.quantity);
                    }

                    // Use the stored initial quantity and add the new quantity
                    let newQuantity = this.initialQuantities[key] + parseFloat(orderline.quantity);

                    // Set the new quantity and update the orderline
                    orderline.set_quantity(newQuantity, product.lst_price);

                    // Move the orderline to the end of the orderlines array
                    product.pos.selectedOrder.orderlines.remove(orderline);
                    product.pos.selectedOrder.orderlines.push(orderline);
            return true;
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
