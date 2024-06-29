/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ErrorBarcodePopup } from "@point_of_sale/app/barcode/error_popup/barcode_error_popup";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { _t } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { Orderline } from "@point_of_sale/app/store/models";

// Patch PosStore to handle multi UOM data
patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.em_uom_list = loadedData['product.multi.uom'];
    },
});

// Patch ProductScreen for barcode action handling
patch(ProductScreen.prototype, {
    async _barcodeProductAction(code) {
        const product = await this._getProductByBarcode(code);
        if (!product) {
            return this.popup.add(ErrorBarcodePopup, { code: code.base_code });
        }
        const options = await product.getAddProductOptions(code);
        if (!options) {
            return;
        }

        // Update options based on scanned code type
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

        // Add product to current order with updated options
        this.currentOrder.add_product(product, options);

        // Handle multi UOM scenarios
        const pos_multi_op = this.pos.em_uom_list;
        let is_multi_uom = false;
        let unit_price = 0;
        for (let i = 0; i < pos_multi_op.length; i++) {
            if (pos_multi_op[i].barcode == code.base_code) {
                unit_price = pos_multi_op[i].price;
                is_multi_uom = true;
                Object.assign(options, {
                    price: pos_multi_op[i].price,
                    extras: {
                        wvproduct_uom: this.pos.units_by_id[pos_multi_op[i].multi_uom_id[0]],
                    },
                });
            }
        }

        // Add product again if multi UOM applies and set unit price
        this.currentOrder.add_product(product, options);
        if (is_multi_uom) {
            const line = this.currentOrder.selected_orderline;
            line.set_unit_price(unit_price);
        }

        // Reset buffer after processing
        this.numberBuffer.reset();
    }
});

// Patch Orderline for handling product UOM
patch(Orderline.prototype, {
    setup() {
        super.setup(...arguments);
        this.wvproduct_uom = '';
    },

    set_product_uom(uom_id) {
        this.wvproduct_uom = this.pos.units_by_id[uom_id];
    },

    get_unit() {
        const unit_id = this.product.uom_id;
        if (!unit_id) {
            return undefined;
        }
        return this.wvproduct_uom == '' ? this.pos.units_by_id[unit_id[0]] : this.wvproduct_uom;
    },

    export_as_JSON() {
        const unit_id = this.product.uom_id;
        const json = super.export_as_JSON(...arguments);
        json.product_uom = this.wvproduct_uom == '' ? unit_id[0] : this.wvproduct_uom.id;
        return json;
    },

    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.wvproduct_uom = json.wvproduct_uom;
    },

    can_be_merged_with(orderline) {
        const result = super.can_be_merged_with(...arguments);
        return result && this.wvproduct_uom.id != orderline.wvproduct_uom.id;
    },
});

// Define multi UOM widget for popup interaction
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

// Define button component for changing UOM
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
        for (let i = 0; i < em_uom_list.length; i++) {
            if (multi_uom_ids.indexOf(em_uom_list[i].id) >= 0) {
                modifiers_list.push(em_uom_list[i]);
            }
        }

        const { confirmed, payload: inputNote } = await this.popup.add(MulitUOMWidget, {
            startingValue: selectedOrderline.get_customer_note(),
            title: _t("POS Multi UOM"),
            modifiers_list,
        });

        // Handle confirmed action if needed
    }
}

// Define button component for refund operation
export class RefundButton extends Component {
    static template = "point_of_sale.RefundButton";

    setup() {
        this.pos = usePos();
    }

    click() {
        const order = this.pos.get_order();
        const partner = order.get_partner();
        const searchDetails = partner ? { fieldName: "PARTNER", searchTerm: partner.name } : {};
        this.pos.showScreen("TicketScreen", {
            ui: { filter: "SYNCED", searchDetails },
            destinationOrder: order,
            multiUomData: this.pos.em_uom_list,
        });
    }
}

// Add control buttons to ProductScreen based on conditions
ProductScreen.addControlButton({
    component: ChangeUOMButton,
    condition: function() {
        return this.pos.config.allow_multi_uom;
    },
});

ProductScreen.addControlButton({
    component: RefundButton,
    condition: function() {
        return this.pos.config.allow_multi_uom;
    },
});
