odoo.define('pos_default_customer.models', function (require) {
    'use strict';

    const models = require('point_of_sale.models');

    models.load_fields('res.partner', ['id']);

    const _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            _super_order.initialize.apply(this, arguments);
            const default_customer_id = this.pos.config.default_customer_id;
            if (default_customer_id) {
                const default_customer = this.pos.db.get_partner_by_id(default_customer_id[0]);
                if (default_customer) {
                    this.set_client(default_customer);
                }
            }
        },
    });
});
