odoo.define('ksa_zatca_integration_pos.ReceiptScreen', function (require) {
    'use strict';

    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const Registries = require('point_of_sale.Registries');
    const { onMounted, useRef, status } = owl;

    const ZatcaReceiptScreen = (ReceiptScreen_) =>
        class extends ReceiptScreen_ {
            setup() {
                super.setup();
                onMounted(() => {
                    var self = this;
                    self.onMounted();
                });
            }
            onMounted() {
                var self = this;
                self.has_auto_print = 0
                if (self._shouldAutoPrint()){
                    self.currentOrder._printed = true;
                    self.has_auto_print = 1
                }
                $(this.el).find('.pos-receipt-container').html('<br/><br/><br/><br/><br/><br/><br/><br/><br/><h1>Rendering</h1><h2>Receipt</h2><h3>.</h3>');
                $(this.orderReceipt.el).html('');
                setTimeout(async () => {
                    try {
                        $(self.el).find('.pos-receipt-container').html('<br/><br/><br/><br/><br/><br/><br/><br/><br/><h1>Rendering</h1><h2>Receipt</h2><h3>..</h3>');
                        let response = await self.rpc({
                            model: 'pos.order',
                            method: 'get_simplified_zatca_report',
                            args: [[], self.currentOrder.name],
                        });
                        $(this.el).find('.pos-receipt-container').html('<br/><br/><br/><br/><br/><br/><br/><br/><br/><h1>Rendering</h1><h2>Receipt</h2><h3>...</h3>');
                        response = $($(response)).find('.pos-receipt').parent().html();
                        $(self.el).find('.pos-receipt-container').html(response);
                        $(self.orderReceipt.el).html(response);
                        var message = "Sending to ZATCA ..."
                        var zatca_status_box = "<style>.zatca_status *{font-size: 12px !important;}</style>"
                        zatca_status_box += "<div class='notice zatca_status' style='overflow: auto;border: 1px solid darkgrey;padding: 5px;'><center style='width: 100%;'><b> " + message + " </b></center></div>"

                        if (self.has_auto_print){
                            self.currentOrder._printed = false;
                            setTimeout(async () => {
                                let images = self.orderReceipt.el.getElementsByTagName('img');
                                for (let image of images) {
                                    await image.decode();
                                }
                                await self.handleAutoPrint();
                            }, 0);
                        }

                        if (self.env.pos.company.zatca_send_from_pos && !self.currentOrder.sent_to_zatca){
                            $(self.el).find('.actions').append(zatca_status_box);
                            try {
                                let zatca_response = await self.rpc({
                                    model: 'pos.order',
                                    method: 'send_to_zatca',
                                    args: [[], self.currentOrder.name],
                                });
                                if (zatca_response.hasOwnProperty('name') && zatca_response.name == 'Zatca Response')
                                    message = "Successfully send to ZATCA"
                                else
                                    message = zatca_response
                                zatca_status_box = "<div class='notice zatca_status' style='border: 1px solid darkgrey;padding: 5px;'><center style='width: 100%;'><b> " + message + " </b></center></div>"
                                $(self.el).find('.zatca_status').remove();
                                $(self.el).find('.actions')[0].style.overflow = 'auto'
                                $(self.el).find('.actions').append(zatca_status_box);
                                self.currentOrder.sent_to_zatca = true;
                            }
                            catch (error) {
                                $(self.el).find('.zatca_status').remove();
                                var message = "Sending to ZATCA FAILED."
                                var zatca_status_box = "<style>.zatca_status *{font-size: 12px !important;}</style>"
                                zatca_status_box += "<div class='notice zatca_status' style='overflow: auto;border: 1px solid darkgrey;padding: 5px;'><center style='width: 100%;'><b> " + message + " </b></center></div>"
                                $(self.el).find('.actions').append(zatca_status_box);


                                if (['object', 'string'].find((str) => str === typeof(error.message)) != undefined)
                                    await self.showPopup('ErrorPopup', {
                                        title: "500 internal server error",
                                        body: self.env._t(error.message),
                                    });
                                else
                                    await self.showPopup('ErrorPopup', {
                                        title: self.env._t(error.message.message),
                                        body: self.env._t(error.message.data.message),
                                    });
                            }
                        }
                        else {
                            if (self.currentOrder.sent_to_zatca){
                                $(self.el).find('.zatca_status').remove();
                                var message = "Already sent to ZATCA."
                                var zatca_status_box = "<style>.zatca_status *{font-size: 12px !important;}</style>"
                                zatca_status_box += "<div class='notice zatca_status' style='overflow: auto;border: 1px solid darkgrey;padding: 5px;'><center style='width: 100%;'><b> " + message + " </b></center></div>"
                                $(self.el).find('.actions').append(zatca_status_box);
                            }
                            else {
                                $(self.el).find('.zatca_status').remove();
                                var message = "auto send to ZATCA disabled.<br/> send it from invoice."
                                var zatca_status_box = "<style>.zatca_status *{font-size: 12px !important;}</style>"
                                zatca_status_box += "<div class='notice zatca_status' style='overflow: auto;border: 1px solid darkgrey;padding: 5px;'><center style='width: 100%;'><b> " + message + " </b></center></div>"
                                $(self.el).find('.actions').append(zatca_status_box);
                            }

                        }
                    } catch (error) {
                        if (['object', 'string'].find((str) => str === typeof(error.message)) != undefined)
                            await self.showPopup('ErrorPopup', {
                                title: "500 internal server error",
                                body: self.env._t(error.message),
                            });
                        else
                            await self.showPopup('ErrorPopup', {
                                title: self.env._t(error.message.message),
                                body: self.env._t(error.message.data.message),
                            });
                    }
                }, 0);
              }
        };

    Registries.Component.extend(ReceiptScreen, ZatcaReceiptScreen);

    return ReceiptScreen;
});
