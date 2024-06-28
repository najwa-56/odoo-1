/** @odoo-module */

import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { ConnectionLostError, ConnectionAbortedError } from "@web/core/network/rpc_service";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { onRendered } from "@odoo/owl";

patch(OrderReceipt.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
//        onMounted(this.onMounted);
        onRendered(async() => await this.onRendered());
    },
    async get_report(name) {
        let response = await this.orm.call('pos.order', 'get_simplified_zatca_report', [[], name]);
        if (response)
            response = $($(response)).find('.pos-receipt').parent().html()
        return response
    },
    async onRendered() {
        var self = this;
        if (this.env.services.pos.company.parent_is_zatca){
            this.constructor.template = 'ksa.ZatcaSimplified';
            try {
                let response = await this.get_report(this.props.data.name)
                if (response){
                    $($('.pos-receipt-container').children()[0]).html(response)
                    if (this.env.services.pos.company.parent_zatca_send_from_pos &&
                        !['ReprintReceiptScreen', 'RenderContainer'].includes(this.__owl__.parent.name) &&
                        !this.__owl__.parent.component?.currentOrder?.sent_to_zatca){
                        await this.send_to_zatca();
                    }
                    else{
                        if (['ReprintReceiptScreen', 'RenderContainer'].includes(this.__owl__.parent.name)){
                        }
                        else if (this.__owl__.parent.component.currentOrder.sent_to_zatca){
                            var message = "Already sent to ZATCA."
                            if (['Sending to ZATCA ...', ''].includes($('.zatca_status_details').html()))
                                $('.zatca_status_details').html(message);
                        }
                        else {
                            var message = "auto send to ZATCA disabled.<br/> send it from invoice."
                            $('.zatca_status_details').html(message);
                        }
                    }
                }
                else {
                    $($('.pos-receipt-container').children()[0]).html('<h1>No Invoice Found.</h1>')
                }
            } catch (error) {
                if (error instanceof ConnectionLostError || error instanceof ConnectionAbortedError)
                    $($('.pos-receipt-container').children()[0]).html('<h1>Network Error.</h1>')
                Promise.reject(error);
            }
        }
    },
    async send_to_zatca(){
        var message = "Sending to ZATCA ..."
        $('.zatca_status_details').html(message);
        try{
            let zatca_response = await this.orm.call('pos.order', 'send_to_zatca', [[], this.props.data.name]);
            if (zatca_response.hasOwnProperty('name') && zatca_response.name == 'Zatca Response')
                message = "Successfully send to ZATCA"
            else
                message = zatca_response
//            $(self.el).find('.actions')[0].style.overflow = 'auto'
            $('.zatca_status_details').html(message);
            this.__owl__.parent.component.currentOrder.sent_to_zatca = true;
        }
        catch (error){
            var message = "Sending to ZATCA FAILED."
            $('.zatca_status_details').html(message);


            if (['object', 'string'].find((str) => str === typeof(error.message)) != undefined)
                this.popup.add(ErrorPopup, {
                    title: _t("500 internal server error"),
                    body: _t(error.message),
                });
            else
                this.popup.add(ErrorPopup, {
                    title: _t(error.message.message),
                    body: _t(error.message.data.message),
                });
        }
    },
});
