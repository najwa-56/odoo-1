/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ErrorBarcodePopup } from "@point_of_sale/app/barcode/error_popup/barcode_error_popup";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { _t } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { TextAreaPopup } from "@point_of_sale/app/utils/input_popups/textarea_popup";
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { onMounted, useRef, useState } from "@odoo/owl";
import { PosDB } from "@point_of_sale/app/store/db";
import { Order, Orderline, Payment } from "@point_of_sale/app/store/models";
import {
    formatFloat,
    roundDecimals as round_di,
    roundPrecision as round_pr,
    floatIsZero,
} from "@web/core/utils/numbers";

// Patch for PosStore to process data
patch(PosStore.prototype, "em_pos_multi_uom", {
    async _processData(loadedData) {
        await this._super(...arguments);
        this.em_uom_list = loadedData['product.multi.uom'] || [];
    },
});

// Patch for PosDB to add products
patch(PosDB.prototype, "em_pos_multi_uom", {
    add_products(products) {
        this._super(...arguments);
        for (const product of products) {
            if (product.has_multi_uom && product.multi_uom_ids) {
                const barcode_list = JSON.parse(product.new_barcode);
                for (const barcode of barcode_list) {
                    this.product_by_barcode[barcode] = product;
                }
            }
        }
    },
});

// Patch for ProductScreen to handle barcode product action
patch(ProductScreen.prototype, "em_pos_multi_uom", {
    async _barcodeProductAction(code) {
        const product = await this._getProductByBarcode(code);
        if (!product) {
            return this.popup.add(ErrorBarcodePopup, { code: code.base_code });
        }
        const options = await product.getAddProductOptions(code);
        if (!options) return;

        // Update options based on the type of scanned code
        if (code.type === "price") {
            Object.assign(options, {
                price: code.value,
                extras: { price_type: "manual" },
            });
        } else if (["weight", "quantity"].includes(code.type)) {
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

        if (this.env.pos.em_uom_list && Array.isArray(this.env.pos.em_uom_list)) {
            const pos_multi_op = this.env.pos.em_uom_list;
            let is_multi_uom = false;
            let unit_price = 0;

            for (const op of pos_multi_op) {
                if (op.barcode === code.base_code) {
                    unit_price = op.price;
                    is_multi_uom = true;
                    Object.assign(options, {
                        price: op.price,
                        extras: {
                            wvproduct_uom: this.env.pos.units_by_id[op.multi_uom_id[0]],
                        },
                    });
                    break;
                }
            }

            this.currentOrder.add_product(product, options);
            if (is_multi_uom) {
                const line = this.currentOrder.selected_orderline;
                line.set_unit_price(unit_price);
            }
        } else {
            console.error('em_uom_list is not defined or not an array');
        }

        this.numberBuffer.reset();
    },
});

// Patch for Orderline to handle custom unit of measure logic
patch(Orderline.prototype, "em_pos_multi_uom", {
    setup() {
        this._super(...arguments);
        this.wvproduct_uom = '';
    },

    set_product_uom(uom_id) {
        this.wvproduct_uom = this.pos.units_by_id[uom_id];
    },

    get_unit() {
        const unit_id = this.product.uom_id[0];
        return this.wvproduct_uom === '' ? this.pos.units_by_id[unit_id] : this.wvproduct_uom;
    },

    export_as_JSON() {
        const json = this._super(...arguments);
        json.product_uom = this.wvproduct_uom === '' ? this.product.uom_id[0] : this.wvproduct_uom.id;
        return json;
    },

    init_from_JSON(json) {
        this._super(...arguments);
        this.wvproduct_uom = json.wvproduct_uom;
    },

    can_be_merged_with(orderline) {
        const result = this._super(...arguments);
        if (result && this.wvproduct_uom.id !== orderline.wvproduct_uom.id) {
            return false;
        }
        return result;
    },
});

// Define MultiUOMWidget component
export class MulitUOMWidget extends AbstractAwaitablePopup {
    static template = "em_pos_multi_uom.MulitUOMWidget";
    static defaultProps = {
        confirmText: _t("Add"),
        cancelText: _t("Discard"),
        title: "",
        body: "",
    };

    setup() {
        super.setup();
        this.state = useState({ inputValue: this.props.startingValue });
    }

    multi_uom_button(event) {
        const uom_id = $(event.target).data('uom_id');
        const price = $(event.target).data('price');
        const line = this.env.services.pos.get_order().get_selected_orderline();
        if (line) {
            line.set_unit_price(price);
            line.set_product_uom(uom_id);
            line.price_manually_set = true;
        }
        this.cancel();
    }
}

// Define ChangeUOMButton component
export class ChangeUOMButton extends Component {
    static template = "em_pos_multi_uom.ChangeUOMButton";

    setup() {
        this.pos = usePos();
        this.popup = useService("popup");
    }

    async onClick() {
        const selectedOrderline = this.pos.get_order().get_selected_orderline();
        if (!selectedOrderline) {
            return;
        }

        const modifiers_list = [];
        const product = selectedOrderline.get_product();
        const em_uom_list = this.pos.em_uom_list;
        const multi_uom_ids = product.multi_uom_ids;

        for (const uom of em_uom_list) {
            if (multi_uom_ids.includes(uom.id)) {
                modifiers_list.push(uom);
            }
        }

        await this.popup.add(MulitUOMWidget, {
            startingValue: selectedOrderline.get_customer_note(),
            title: _t("POS Multi UOM"),
            modifiers_list: modifiers_list,
        });
    }
}

// Add ChangeUOMButton to the ProductScreen
ProductScreen.addControlButton({
    component: ChangeUOMButton,
    condition: function () {
        return this.pos.config.allow_multi_uom;
    },
});
