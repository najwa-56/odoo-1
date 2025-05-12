/** @odoo-module */

import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { ConnectionLostError, ConnectionAbortedError } from "@web/core/network/rpc_service";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";

import { onRendered } from "@odoo/owl";

patch(OrderReceipt.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.pos = usePos();
//        onMounted(this.onMounted);
        //onRendered(async() => await this.onRendered());
    },
    get config(){
    	return this.pos.config;
    },

  	get order() {
  		return this.pos.get_order();
	},

	get orderlines() {
        const orderlines = this.pos.get_order().get_orderlines();
        // Return false if the orderlines array is empty
        return orderlines.length === 0 ? false : orderlines;
	},

	get partner() {
		return this.pos.get_order().get_partner();
	},
    

});
