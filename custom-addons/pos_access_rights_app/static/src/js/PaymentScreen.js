/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { ActionpadWidget } from "@point_of_sale/app/screens/product_screen/action_pad/action_pad";
import { PaymentScreenStatus } from "@point_of_sale/app/screens/payment_screen/payment_status/payment_status";
import { Numpad } from "@point_of_sale/app/generic_components/numpad/numpad";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { reactive, Component, onMounted, onWillStart } from "@odoo/owl";
import { session } from "@web/session";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";

var discount = false;
var plus_minus = false;
var payment = false;
var numpad = false;
var price = false;
var partner = false;
var quantity = false;
var Delete = false;

patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(...arguments);
        await this.user_groups();
    },
    async user_groups(){
        await this.orm.call(
            "pos.session",
            "pos_active_user_group",
            [ , this.user],
        ).then(function (output) {
            discount = output.discount;
            plus_minus = output.plus_minus;
            payment = output.payment;
            quantity = output.quantity;
            numpad = output.numpad;
            price = output.price;
            partner = output.partner;
            Delete = output.Delete;
        })
    }
});

patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
        onMounted(this.onMounted);
    },
    onMounted() {
        if (partner == true){
            $('.partner-button').find('.button').prop('disabled', true);
            $('.partner-button').css('background-color', 'lightgrey');
            $('.partner-button').find('.button').css('background-color', 'lightgrey');
        }
    },
    async selectPartner(isEditMode = false, missingFields = []) {
        if (partner == false){
            const currentPartner = this.currentOrder.get_partner();
            const partnerScreenProps = { partner: currentPartner };
            if (isEditMode && currentPartner) {
                partnerScreenProps.editModeProps = true;
                partnerScreenProps.missingFields = missingFields;
            }
            const { confirmed, payload: newPartner } = await this.pos.showTempScreen(
                "PartnerListScreen",
                partnerScreenProps
            );
            if (confirmed) {
                this.currentOrder.set_partner(newPartner);
            }
        }
    }
});

patch(ActionpadWidget.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
        onMounted(this.onMounted);
    },
    onMounted() {
        if (partner == true){
            $('.set-partner').prop('disabled', true);
            $('.set-partner').css('background-color', '#b6b6b6');
        }
        if (payment == true){
            $('.pay').prop('disabled', true);
            $('.pay').css('background-color', '#b6b6b6');
            $('.pay').css('color', 'black');
        }
    }
});

patch(ProductScreen.prototype, {
    onNumpadClick(buttonValue) {
        if (buttonValue == 'discount'){
            if (discount == false){
                if (["quantity", "discount", "price"].includes(buttonValue)) {
                    this.numberBuffer.capture();
                    this.numberBuffer.reset();
                    this.pos.numpadMode = buttonValue;
                    return;
                }
                this.numberBuffer.sendKey(buttonValue);
            }
        }

        if (buttonValue == 'price'){
            if (price == false){
                if (["quantity", "discount", "price"].includes(buttonValue)) {
                    this.numberBuffer.capture();
                    this.numberBuffer.reset();
                    this.pos.numpadMode = buttonValue;
                    return;
                }
                this.numberBuffer.sendKey(buttonValue);
            }
        }

        if (buttonValue == 'quantity'){
            if (quantity == false){
                if (["quantity", "discount", "price"].includes(buttonValue)) {
                    this.numberBuffer.capture();
                    this.numberBuffer.reset();
                    this.pos.numpadMode = buttonValue;
                    return;
                }
                this.numberBuffer.sendKey(buttonValue);
            }
        }
        if (["1", "2", "3", "4", "5", "6", "7", "8", "9", ".", "0"].includes(buttonValue)) {
            if (numpad == false){
                if (["quantity", "discount", "price"].includes(buttonValue)) {
                    this.numberBuffer.capture();
                    this.numberBuffer.reset();
                    this.pos.numpadMode = buttonValue;
                    return;
                }
                this.numberBuffer.sendKey(buttonValue);
            }
        }
        if (["-", "+"].includes(buttonValue)) {
            if (plus_minus == false){
                if (["quantity", "discount", "price"].includes(buttonValue)) {
                    this.numberBuffer.capture();
                    this.numberBuffer.reset();
                    this.pos.numpadMode = buttonValue;
                    return;
                }
                this.numberBuffer.sendKey(buttonValue);
            }
        }
        /* I add this method to enable delete*/
        if (["Backspace", "⌫"].includes(buttonValue)) {
            if (Delete == false){
                if (["quantity", "discount", "price"].includes(buttonValue)) {
                    this.numberBuffer.capture();
                    this.numberBuffer.reset();
                    this.pos.numpadMode = buttonValue;
                    return;
                }
                this.numberBuffer.sendKey(buttonValue);
            }else {
                // Add this new condition
                const result = this.order.get_current_order().get_selected_orderline().set_quantity(0);
                if (!result) {
                    this.env.services.popup.add(ErrorPopup, {
                        title: _t("Quantity Error"),
                        body: _t("Quantity cannot be set to zero."),
                    });
                }}
        }

    }
});