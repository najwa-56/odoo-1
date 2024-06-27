odoo.define('ksa_zatca_integration_pos.PaymentScreen', function (require) {
    'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');

    const ZatcaPaymentScreen = (PaymentScreen_) =>
          class extends PaymentScreen_ {
              constructor() {
                super(...arguments);
                if (!this.currentOrder.is_to_invoice())
                    this.toggleIsToInvoice();
              }
              async _finalizeValidation() {
                if (this.currentOrder.get_total_with_tax() < 0 && _.contains([undefined, false, NaN, ''], this.currentOrder.credit_debit_reason))
                    await this.showPopup('ErrorPopup', {
                        title: this.env._t('Zatca Validation Error'),
                        body: this.env._t(
                            'reason is compulsory for returns for zatca.'
                        ),
                    });
                else
                    if (this.currentOrder.is_to_invoice())
                      await super._finalizeValidation();
                    else
                        await this.showPopup('ErrorPopup', {
                            title: this.env._t('Zatca Validation Error'),
                            body: this.env._t(
                                'Invoice is compulsory for zatca.'
                            ),
                        });
              }
              toggleIsThirdParty() {
                this.currentOrder.l10n_is_third_party_invoice = this.currentOrder.l10n_is_third_party_invoice ? 0 : 1
                this.render();
              }
              toggleIsNominal() {
                this.currentOrder.l10n_is_nominal_invoice = this.currentOrder.l10n_is_nominal_invoice ? 0 : 1
                this.render();
              }
              toggleIsSummary() {
                this.currentOrder.l10n_is_summary_invoice = this.currentOrder.l10n_is_summary_invoice ? 0 : 1
                this.render();
              }
              Refund_Reason() {
                this.currentOrder.credit_debit_reason = arguments[0].currentTarget.value;
              }

          };

    Registries.Component.extend(PaymentScreen, ZatcaPaymentScreen);

    return PaymentScreen;
});
