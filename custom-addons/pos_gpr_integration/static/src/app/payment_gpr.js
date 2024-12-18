/** @odoo-module */

/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { Payment } from "@point_of_sale/app/store/models";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

var is_open_socket = false;
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
class WkErrorNotifyPopopWidget extends AbstractAwaitablePopup {}
WkErrorNotifyPopopWidget.template = 'pos_gpr_integration.WkErrorNotifyPopopWidget';
WkErrorNotifyPopopWidget.defaultProps = { title: 'Error !!!', value: '' };

patch(Payment.prototype, {
    setup() {
        super.setup(...arguments);
        this.gpr_data = this.gpr_data || false;
        this.approval_code = this.approval_code || '';
    },
    //@override
    export_as_JSON() {
        let data = super.export_as_JSON(...arguments);
        return Object.assign(data, {
            gpr_data: this.gpr_data,
            approval_code: this.approval_code,
        });
    },
    //@override
    iinit_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.gpr_data = json.gpr_data;
        this.approval_code = json.approval_code;
    }

});

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        if (!this.env.services.pos.socket) {
            this.open_socket();
        } else if (!is_open_socket) {
            is_open_socket = true;
            this.open_socket();
        }
    },

    async _sendGprRequest({ detail: line }) {
        this.paymentLines.forEach(function (line) {
            line.can_be_reversed = false;
        });

        const payment_terminal = line.payment_method.payment_terminal;
        payment_terminal._gpr_pay();
    },

    handleCOMDisConnect() {
        let comName = "COM10";
        this.sendData(
            JSON.stringify({
                Event: "CONNECTION",
                Operation: "DISCONNECT",
                connectionMode: "COM",
                comName,
                braudRate: "38400",
                dataBits: "8",
                parity: "none",
            })
        );
    },

    sendData(data) {
        var wsUrl = this.env.services.pos.temp_url || "ws://localhost:5000/messages";
        var env = this.env;
        if (!this.env.services.pos.socket) {
            var socket = new WebSocket(wsUrl);
            socket.onopen = function () {
                console.log("ws.onopen");
            };

            socket.onclose = function () {
                env.services.pos.message += "\n ws.onclose";
                console.log("ws.onclose ");
            };

            socket.onerror = function (error) {
                env.services.pos.message += "\n ws.onerror : " + error.message;
                console.log("ws.onerror : " + error.message);
            };

            socket.onmessage = function (data) {
                env.services.pos.message += "\n received : " + JSON.stringify(JSON.parse(data.data));
                console.log("data received", data);
            };
            console.log({ data }, "sent");
            return socket.send(data);
        } else {
            var socket = this.env.services.pos.socket;
            return socket.send(data);
        }
    },

    open_socket(data) {
        var wsUrl = this.env.services.pos.temp_url || "ws://localhost:5000/messages";
        var socket = new WebSocket(wsUrl);
        var env = this.env;
        this.env.services.pos.socket = socket;
        socket.onopen = function () {
            console.log("pos socket on open");
        };

        socket.onclose = function () {
            env.services.pos.pos_message += "\n ws.onclose";
            console.log(" pos on .onclose ");
        };

        socket.onerror = function (error) {
            console.log("this=-===",this)
            env.services.pos.pos_message += "\n ws.onerror : " + error.message;
            console.log("pos ws.onerror : " + error.message);
        };

        socket.onmessage = function (data) {
            let temp_data = null;
            if (data) {
                temp_data = JSON.parse(data.data);
                let error_event = data.Event && data.Event == 'OnError' ? 'error' : '';
                if (error_event == '') {
                    error_event = temp_data && temp_data.Event && temp_data.Event == 'OnError' ? 'error' : '';
                }
                if (error_event == 'error' && temp_data && temp_data.Message && temp_data.Message.indexOf('port is closed') >= 0) {
                    this.env.services.popup.add(ErrorPopup, {
                        'title': 'Connection Error',
                        'body': 'Terminal is not connected'
                    });
                    $.unblockUI();
                    return Promise.reject(temp_data);
                }
                if (temp_data && temp_data.EventName) {
                    if (temp_data.EventName == 'TERMINAL_RESPONSE') {
                        console.log("terminal response", temp_data);
                        var paymentline = env.services.pos.get_order().selected_paymentline;
                        var termi_resp = JSON.parse(temp_data.JsonResult);
                        if (termi_resp && termi_resp.TransactionResponseEnglish) {
                            $.unblockUI();
                            if (termi_resp.TransactionResponseEnglish == 'APPROVED') {
                                if (termi_resp.TransactionAmount && termi_resp.TransactionAmount != paymentline.amount) {
                                    var wk_line = env.services.pos.get_order().selected_paymentline;
                                    if (wk_line && wk_line.time_interval)
                                        clearInterval(wk_line.time_interval);
                                    this.env.services.popup.add(ErrorPopup, {
                                        'title': 'Terminal Return Wrong Amount',
                                        'body': 'Return Amount is not matched with the amount entered. Please proceed again'
                                    });
                                } else {
                                    paymentline.status = true;
                                    paymentline.payment_pending = false;
                                    paymentline.gpr_scan_pending = false;
                                    paymentline.gpr_data = temp_data.JsonResult;
                                    paymentline.payment_type = temp_data.CardNameEnglish;
                                    paymentline.approval_code = temp_data.TransactionAuthCode;
                                    paymentline.set_payment_status('done');
                                    if (paymentline.time_interval)
                                        clearInterval(paymentline.time_interval);
                                    $.unblockUI();
                                }
                            } else {
                                this.env.services.popup.add(ErrorPopup, {
                                    'title': 'Transaction Error',
                                    'body': termi_resp.TransactionResponseEnglish
                                });
                            }
                            var wk_line = this.env.services.pos.get_order().selected_paymentline;
                            if (wk_line && wk_line.time_interval)
                                clearInterval(wk_line.time_interval);
                        }
                    } else if (temp_data.EventName == 'TERMINAL_ACTION') {
                        if (temp_data.TerminalAction == 'USER_CANCELLED_AND_TIMEOUT') {
                            $.unblockUI();
                            this.env.services.popup.add(ErrorPopup, {
                                'title': temp_data.OptionalMessage,
                                'body': ''
                            });
                            var wk_line = env.services.pos.get_order().selected_paymentline;
                            if (wk_line && wk_line.time_interval)
                                clearInterval(wk_line.time_interval);
                            return Promise.reject(temp_data);
                        }
                    }
                }
            }
        }.bind(this);
    }
});

export class Paymentgpr extends PaymentInterface {
    send_payment_request(cid) {

        var payment_line = this.pos.get_order().selected_paymentline;
        if (payment_line.gpr_data) {
            return 1;
        } else {
            super.send_payment_request(cid);
            this._gpr_pay()
        }
    }

    handleCOMDisConnect(){
        let comName = this.payment_method.gpr_api_key || "COM10";
            this.sendData(
                JSON.stringify({
                    Event: "CONNECTION",
                    Operation: "DISCONNECT",
                    connectionMode: "COM",
                    comName,
                    braudRate: "38400",
                    dataBits: "8",
                    parity: "none",
                })
            );
        }
    handleCOMConnect(){
        let comName = this.payment_method.gpr_api_key || "COM10";
        this.sendData(
            JSON.stringify({
                Event: "CONNECTION",
                Operation: "CONNECT",
                connectionMode: "COM",
                comName,
                braudRate: "38400",
                dataBits: "8",
                parity: "none",
            })
        );
    }

    initPurchaseTransaction(amount){
        console.log("startinitPurchaseTransaction ")
        this.pos.gpr_self = this;
           return  this.sendData(
                JSON.stringify({
                Event: "TRANSACTION",
                Operation: "PURCHASE",
                Amount: amount,
                PrintSettings: "1",
                AppId: "11",
                ECRNumber: "1234567890123456",
                })
            );
    }

    open_socket(data){
        var wsUrl = this.pos.temp_url || "ws://localhost:5000/messages";
        var socket = new WebSocket(wsUrl);
        this.pos.socket = socket;
        var self = this;
        socket.onopen = function () {
            let request = document.querySelector("#request");
//                 request.innerHTML += "\n ws.onopen";

//                 console.log("ws.onopen");
            console.log("pos socker on open")
        };

        socket.onclose = function () {
            // let response = document.querySelector("#response");
            self.pos.pos_message += "\n ws.onclose";
            console.log(" pos on .onclose ");
        };

        socket.onerror = function (error) {
            self.pos.pos_message += "\n ws.onerror : " + error.message;
            console.log("pos ws.onerror : " + error.message);
        };

        socket.onmessage = function (data) {
            let temp_data = null;
            if(data){
                temp_data = JSON.parse(data.data);

            console.log("temp_data",temp_data)
            let error_event = data.Event && data.Event == 'OnError' ? 'error' : '';

            if (error_event == ''){
                error_event = temp_data && temp_data.Event && temp_data.Event == 'OnError' ? 'error' : '';

            }
            console.log("error_event----------------",error_event)
            if(error_event == 'error' && temp_data && temp_data.Message && temp_data.Message.indexOf('port is closed') >=0){
              console.log("popup need to show of errpr")
                this.env.services.popup.add(ErrorPopup,{
                    'title': 'Connection Error',
                    'body': 'Terminal is not conneted'
                });


                $.unblockUI();
                self.handleCOMDisConnect()
                return  Promise.reject(temp_data)
            }

            if(temp_data && temp_data.EventName){
                if(temp_data.EventName=='TERMINAL_RESPONSE'){

                    console.log("terminal response",temp_data);
                    var paymentline = self.pos.get_order().selected_paymentline;
                    var  termi_resp = JSON.parse(temp_data.JsonResult)
                    if(termi_resp && termi_resp.TransactionResponseEnglish){
                        $.unblockUI();
                        if(termi_resp.TransactionResponseEnglish =='APPROVED' ){

                            if(termi_resp.TransactionAmount && termi_resp.TransactionAmount != paymentline.amount ){
                                self.handleCOMDisConnect()
                                var wk_line = self.pos.get_order().selected_paymentline
                                if(wk_line && wk_line.time_interval)
                                    clearInterval(wk_line.time_interval)
                                    this.env.services.popup.add(ErrorPopup,{
                                        'title': 'Terminal Return Wrong Amount',
                                        'body': 'Return Amount is not matched with the amount entered. Please proceed again'
                                    });


                            }
                            else{
                                paymentline.status = true;
                                paymentline.payment_pending = false;
                                paymentline.gpr_scan_pending = false;
                                paymentline.gpr_data = temp_data.JsonResult;
                                paymentline.payment_type = temp_data.CardNameEnglish;
                                paymentline.approval_code = temp_data.TransactionAuthCode;
                                paymentline.set_payment_status('done');
                                if(paymentline.time_interval)
                                    clearInterval(paymentline.time_interval)
                                $.unblockUI()

                            }
                        }
                        else{

                            this.env.services.popup.add(ErrorPopup,{
                                'title': 'Transaction Error',
                                'body': termi_resp.TransactionResponseEnglish
                            });

                        }

                // self.handleCOMDisConnect()
                var wk_line = self.pos.get_order().selected_paymentline
                        if(wk_line && wk_line.time_interval)
                            clearInterval(wk_line.time_interval)

                    }
                }
                else if(temp_data.EventName =='TERMINAL_ACTION'){
                    if(temp_data.TerminalAction == 'USER_CANCELLED_AND_TIMEOUT'){
                        $.unblockUI();

                        this.env.services.popup.add(ErrorPopup,{
                            'title': temp_data.OptionalMessage,
                            'body': ''
                        });

                        var wk_line = self.pos.get_order().selected_paymentline
                        if(wk_line && wk_line.time_interval)
                            clearInterval(wk_line.time_interval)

                    }

                }
                }
            }
        };
    }

    sendData(data){
        console.log("data===========",data)
        var wsUrl = this.pos.temp_url || "ws://localhost:5000/messages";
        if(!this.pos.socket){
            var socket = new WebSocket(wsUrl);
            var self = this;
            socket.onopen = function () {
                let request = document.querySelector("#request");
                console.log("ws.onopen");
            };

            socket.onclose = function () {
                self.pos.message += "\n ws.onclose";
                console.log("ws.onclose ");
            };

            socket.onerror = function (error) {
                self.pos.message += "\n ws.onerror : " + error.message;
                console.log("ws.onerror : " + error.message);
            };

            socket.onmessage = function (data) {
                self.pos.message +="\n received : " + JSON.stringify(JSON.parse(data.data));
                console.log("data received", data);
            };
            console.log({ data }, "sent");
            return socket.send(data);
        }
        else{
            var socket = this.pos.socket;
            return socket.send(data)
        }
    }

    send_payment_cancel(order, cid) {
        super.send_payment_cancel(order, cid);
        this.handleCOMDisConnect();
        return true;
    }

    close() {
        super.close(...arguments);
    }

    _reset_state() {
        this.was_cancelled = false;
        this.last_diagnosis_service_id = false;
        this.remaining_polls = 4;
        clearTimeout(this.polling);
    }

    _handle_odoo_connection_failure(data) {
        var line = this.pos.get_order().selected_paymentline;
        if (line) {
            line.set_payment_status('retry');
        }
        this._show_error('Could not connect to the Odoo server');
    }

    _gpr_pay () {
        var self = this;
        var order = this.pos.get_order();
        if (order.selected_paymentline.amount < 0) {
            this._show_error(('Cannot process transactions with negative amount.'));
            return Promise.resolve(true);
        }
        self.handleCOMConnect();
        $.blockUI({ message: '<h1 class="block_ui_h1"><i class="fa fa-lock"></i>Waiting for terminal response...</h1><center><img id="block_ui_unblock_img" src="/pos_gpr_integration/static/src/img/unlock.png"/></center>' });

        order.selected_paymentline.time_interval = setTimeout(function(){
            $.unblockUI();
            self.handleCOMDisConnect()
            return Promise.resolve(true)
        },60000)

        return self.initPurchaseTransaction(order.selected_paymentline.amount)
    }
}
