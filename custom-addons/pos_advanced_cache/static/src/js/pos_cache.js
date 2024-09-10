odoo.define('pos_advanced_cache.pos_advanced_cache', function (require) {
    "use strict";
    var models = require('point_of_sale.models');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var _t = core._t;

    var posmodel_super = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        load_new_partners: function(){
            var self = this;
            var def  = new $.Deferred();
            var fields = ['name','street','city','state_id','country_id','vat',
                 'phone','zip','mobile','email','barcode','write_date',
                 'property_account_position_id','property_product_pricelist'];
            var domain = [['write_date','>',this.db.get_partner_write_date()]];
            rpc.query({
                    model: 'res.partner',
                    method: 'search_read',
                    args: [domain, fields],
                }, {
                    timeout: 3000,
                    shadow: true,
                })
                .then(function(partners){
                    if (self.db.add_partners(partners)) {   // check if the partners we got were real updates
                        def.resolve();
                    } else {
                        def.reject();
                    }
                }, function(type,err){ def.reject(); });
            return def;
        },
        load_server_data: function () {
            var self = this;
            var product_index = _.findIndex(this.models, function (model) {
                return model.model === "product.product";
            });

            var product_model = self.models[product_index];

            // We don't want to load product.product the normal
            // uncached way, so get rid of it.
            if (product_index !== -1) {
                this.models.splice(product_index, 1);
            }
            return posmodel_super.load_server_data.apply(this, arguments).then(function () {
              // Give both the fields and domain to pos_cache in the
              // backend. This way we don't have to hardcode these
              // values in the backend and they automatically stay in
              // sync with whatever is defined (and maybe extended by
              // other modules) in js.
              var product_fields =  typeof product_model.fields === 'function'  ? product_model.fields(self)  : product_model.fields;
              var product_domain =  typeof product_model.domain === 'function'  ? product_model.domain(self)  : product_model.domain;
                var records = rpc.query({
                        model: 'pos.config',
                        method: 'get_products_from_cache',
                        args: [self.pos_session.config_id[0], product_fields, product_domain],
                    });
                self.setLoadingMessage(_t('Loading') + ' product.product', 1);
                return records.then(function (products) {
                    var new_pro = []
                    for(var i=0;i<products.length;i++){
                        new_pro.push($.parseJSON(products[i][0]))
                    }
                    self.db.add_products(_.map(new_pro, function (product) {
                        product.categ = _.findWhere(self.product_categories, {'id': product.categ_id[0]});
                        product.pos = self;
                        return new models.Product({}, product);
                    }));
                });
            });
        },
    });
    
    var posmodel_super2 = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        load_server_data: function () {
            var self = this;
            var partner_index = _.findIndex(this.models, function (model) {
                return model.model === "res.partner";
            });
            var partner_model = this.models[partner_index];
            var partner_fields = partner_model.fields;
            var partner_domain = partner_model.domain || [];
            if (partner_index !== -1) {
                this.models.splice(partner_index, 1);
            }
            return posmodel_super2.load_server_data.apply(this, arguments).then(function () {
                var records = rpc.query({
                        model: 'pos.config',
                        method: 'get_partner_from_cache',
                        args: [self.pos_session.config_id[0], partner_fields, partner_domain],
                    });
                self.setLoadingMessage(_t('Loading') + 'res.partner', 1);
                return records.then(function (partners) {
                    var new_partner = []
                    for(var i=0;i<partners.length;i++){
                        new_partner.push($.parseJSON(partners[i][0]))
                    }
                    self.db.add_partners(new_partner);
                });
            });
        },
    });
});
