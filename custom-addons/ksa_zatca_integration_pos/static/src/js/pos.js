odoo.define('custom_pos.PosModel', function (require) {
    'use strict';

    const models = require('point_of_sale.models');
    const session = require('web.session');

    models.load_fields('pos.config', ['default_customer_id']);

    const _super_PosModel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            const self = this;
            _super_PosModel.initialize.apply(this, arguments);

            this.ready.then(function () {
                if (self.config.default_customer_id) {
                    const client = self.db.get_partner_by_id(self.config.default_customer_id[0]);
                    if (client) {
                        self.get_order().set_client(client);
                    }
                }
            });
        },
    });
});
