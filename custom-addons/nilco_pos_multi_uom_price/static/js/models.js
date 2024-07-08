/** @odoo-module */
import { Order, Orderline, Payment } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { _t } from "@web/core/l10n/translation";

// Patch the Order prototype
patch(Order.prototype, {
  set_orderline_options(orderline, options) {
    super.set_orderline_options(...arguments);
    if (options.product_uom_id !== undefined) {
      orderline.product_uom_id = options.product_uom_id;
    }
  }
});

// Patch the Orderline prototype
patch(Orderline.prototype, {
  setup(_defaultObj, options) {
    super.setup(...arguments);
    this.product_uom_id = this.product_uom_id || this.product.uom_id;
  },

  export_as_JSON() {
    const json = super.export_as_JSON(...arguments);
    json.product_uom_id = this.product_uom_id[0];
    return json;
  },

  init_from_JSON(json) {
    super.init_from_JSON(...arguments);

    console.log('init_from_JSON:', json);

    if (json.product_uom_id && this.pos && this.pos.units_by_id && this.pos.units_by_id[json.product_uom_id]) {
      this.product_uom_id = {
        0: this.pos.units_by_id[json.product_uom_id].id,
        1: this.pos.units_by_id[json.product_uom_id].name
      };
    } else {
      console.error('Invalid product_uom_id or units_by_id not found', json.product_uom_id, this.pos.units_by_id);
      this.product_uom_id = null;  // or some default value
    }
  },

  set_uom(uom_id) {
    this.product_uom_id = uom_id;
  },

  get_unit() {
    if (this.product_uom_id) {
      var unit_id = this.product_uom_id;
      if (!unit_id) {
        return undefined;
      }
      unit_id = unit_id[0];
      if (!this.pos) {
        return undefined;
      }
      return this.pos.units_by_id[unit_id];
    }
    return this.product.get_unit();
  }
});

// Patch the PosStore prototype
patch(PosStore.prototype, {
  async _processData(loadedData) {
    await super._processData(...arguments);
    this.product_uom_price = loadedData['product.multi.uom.price'];
  }
});

odoo.define('POS Multi UoM Price.PaymentScreen', function(require) {
    'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const { patch } = require('@web/core/utils/patch');
    const { _t } = require('@web/core/l10n/translation');

    patch(PaymentScreen.prototype, {
        _isOrderValid(isForceValidate) {
            const order = this.env.pos.get_order();
            if (!order.get_orderlines().length) {
                this.showPopup('ErrorPopup', {
                    title: _t('Empty Order'),
                    body: _t('There must be at least one product in your order before it can be validated'),
                });
                return false;
            }
            return this._super(isForceValidate);
        }
    });

    return PaymentScreen;
});

