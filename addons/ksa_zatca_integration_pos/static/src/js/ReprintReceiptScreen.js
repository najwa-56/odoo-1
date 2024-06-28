odoo.define('ksa_zatca_integration_pos.ReprintReceiptScreen', function (require) {
    'use strict';

    const ReprintReceiptScreen = require('point_of_sale.ReprintReceiptScreen');
    const Registries = require('point_of_sale.Registries');

    const ZatcaReprintReceiptScreen = (ReprintReceiptScreen_) =>
          class extends ReprintReceiptScreen_ {
              onMounted() {

                var self = this;
                $(this.el).find('.pos-receipt-container').html('<br/><br/><br/><br/><br/><br/><br/><br/><br/><h1>Rendering</h1><h2>Receipt</h2><h3>.</h3>');
                $(this.orderReceipt.el).html('');
                setTimeout(async () => {
                    try {
                        $(this.el).find('.pos-receipt-container').html('<br/><br/><br/><br/><br/><br/><br/><br/><br/><h1>Rendering</h1><h2>Receipt</h2><h3>..</h3>');
                        let response = await self.rpc({
                            model: 'pos.order',
                            method: 'get_simplified_zatca_report',
                            args: [[], self.props.order.name],
                        });
                        $(this.el).find('.pos-receipt-container').html('<br/><br/><br/><br/><br/><br/><br/><br/><br/><h1>Rendering</h1><h2>Receipt</h2><h3>...</h3>');
                        response = $($(response)).find('.pos-receipt').parent().parent().html();
                        $(self.el).find('.pos-receipt-container').html(response);
                        $(self.orderReceipt.el).html(response);
                    } catch (error) {
                        await this.showPopup('ErrorPopup', {
                            title: this.env._t(error.message.message),
                            body: this.env._t(error.message.data.message),
                        });
                    }
                }, 0);

                super.onMounted();
              }
          };

    Registries.Component.extend(ReprintReceiptScreen, ZatcaReprintReceiptScreen);

    return ReprintReceiptScreen;
});
