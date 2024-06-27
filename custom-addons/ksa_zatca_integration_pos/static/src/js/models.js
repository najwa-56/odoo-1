odoo.define('ksa_zatca_integration_pos.models', function (require) {
"use strict";

    var { PosGlobalState, Order } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');

//    models.PosModel = models.PosModel.extend({
//        // saves the order locally and try to send it to the backend and make an invoice
//        // returns a promise that succeeds when the order has been posted and successfully generated
//        // an invoice. This method can fail in various ways:
//        // error-no-client: the order must have an associated partner_id. You can retry to make an invoice once
//        //     this error is solved
//        // error-transfer: there was a connection error during the transfer. You can retry to make the invoice once
//        //     the network connection is up
//
//        push_and_invoice_order: function (order) {
//            var self = this;
//            return new Promise((resolve, reject) => {
//                if (!order.get_client()) {
//                    reject({ code: 400, message: 'Missing Customer', data: {} });
//                } else {
//                    var order_id = self.db.add_order(order.export_as_JSON());
//                    self.flush_mutex.exec(async () => {
//                        try {
//                            const server_ids = await self._flush_orders([self.db.get_order(order_id)], {
//                                timeout: 30000,
//                                to_invoice: true,
//                            });
////                            if (server_ids.length) {
////                                const [orderWithInvoice] = await self.rpc({
////                                    method: 'read',
////                                    model: 'pos.order',
////                                    args: [server_ids, ['account_move']],
////                                    kwargs: { load: false },
////                                });
////                                await self.do_action('account.account_invoices', {
////                                        additional_context: {
////                                            active_ids: [orderWithInvoice.account_move],
////                                        },
////                                    })
////                                    .catch(() => {
////                                        reject({ code: 401, message: 'Backend Invoice', data: { order: order } });
////                                    });
////                            } else {
////                                reject({ code: 401, message: 'Backend Invoice', data: { order: order } });
////                            }
//                            resolve(server_ids);
//                        } catch (error) {
//                            order.finalized = false;
//                            if (error.message.data.debug.includes('ksa_zatca')){
//                                self.db.remove_order(order_id);
//                                self.set_synch('connected', self.db.get_orders().length);
//                            }
////                            reject({ code: 400, message: 'Zatca Error', data: {} });
//                            throw error
////                            this.showPopup('OfflineErrorPopup', {
////                                title: this.env._t('Connection Error'),
////                                body: this.env._t('Order is not synced. Check your internet connection'),
////                            });
////                            reject(error);
//                        }
//                    });
//                }
//            });
//        },
//    });

    const ZatcaOrder = (Order) => class ZatcaOrder extends Order {
        constructor(obj, options) {
            super(...arguments);
        }
        init_from_JSON(json) {
            super.init_from_JSON(...arguments);
            this.l10n_is_third_party_invoice = json.l10n_is_third_party_invoice;
            this.l10n_is_nominal_invoice = json.l10n_is_nominal_invoice;
            this.l10n_is_summary_invoice = json.l10n_is_summary_invoice;
            this.credit_debit_reason = json.credit_debit_reason;
        }
        export_as_JSON() {
            const json = super.export_as_JSON(...arguments);
            json.l10n_is_third_party_invoice = this.l10n_is_third_party_invoice ? 1 : 0;
            json.l10n_is_nominal_invoice = this.l10n_is_nominal_invoice ? 1 : 0;
            json.l10n_is_summary_invoice = this.l10n_is_summary_invoice ? 1 : 0;
            json.credit_debit_reason = this.credit_debit_reason;
            return json;
        }
    }

    Registries.Model.extend(Order, ZatcaOrder);
});
