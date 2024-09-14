//odoo.define('pos_speed_performance.models', function (require) {
//    "use strict";
//
//    var { PosGlobalState } = require('point_of_sale.models');
//    const Registries = require('point_of_sale.Registries');
//
//
//    let PosGlobalStateInherit = PosGlobalState =>
//        class extends PosGlobalState {
//            async loadProductsBackground() {
//                if(this.company.x_allow_online_search){
//                    let products = [];
//                    products = await this.env.services.rpc({
//                        model: 'pos.session',
//                        method: 'get_pos_ui_product_product_by_params',
//                        args: [odoo.pos_session_id, {
//                            offset: 0,
//                            limit: this.company.x_limit_product,
//                        }],
//                    }, { shadow: true });
//                    this._loadProductProduct(products);
//                } else {
//                    let page = 0;
//                    let products = [];
//                    do {
//                        products = await this.env.services.rpc({
//                            model: 'pos.session',
//                            method: 'get_pos_ui_product_product_by_params',
//                            args: [odoo.pos_session_id, {
//                                offset: page * this.config.limited_products_amount,
//                                limit: this.config.limited_products_amount,
//                            }],
//                        }, { shadow: true });
//                        this._loadProductProduct(products);
//                        page += 1;
//                    } while(products.length == this.config.limited_products_amount);
//                }
//
//            }
//
//            async loadPartnersBackground() {
//                if(this.company.x_allow_online_search){
//                    let partners = [];
//                    partners = await this.env.services.rpc({
//                        model: 'pos.session',
//                        method: 'get_pos_ui_res_partner_by_params',
//                        args: [
//                            [odoo.pos_session_id],
//                            {
//                                limit: this.company.x_limit_partner,
//                                offset: 0,
//                            },
//                        ],
//                        context: this.env.session.user_context,
//                    }, { shadow: true });
//                    this.addPartners(partners);
//                } else {
//                    let i = 0;
//                    let partners = [];
//                    do {
//                        partners = await this.env.services.rpc({
//                            model: 'pos.session',
//                            method: 'get_pos_ui_res_partner_by_params',
//                            args: [
//                                [odoo.pos_session_id],
//                                {
//                                    limit: this.config.limited_partners_amount,
//                                    offset: this.config.limited_partners_amount * i,
//                                },
//                            ],
//                            context: this.env.session.user_context,
//                        }, { shadow: true });
//                        this.addPartners(partners);
//                        i += 1;
//                    } while(partners.length);
//                }
//
//            }
//
//            async search_product_to_server(search_key){
//                let products = [];
//                products = await this.env.services.rpc({
//                    model: 'pos.session',
//                    method: 'get_pos_ui_product_product_by_key',
//                    args: [odoo.pos_session_id, {
//                        limit: 5,
//                        search_key: search_key,
//                    }],
//                }, { shadow: true });
//                this._loadProductProduct(products);
//            }
//        }
//    Registries.Model.extend(PosGlobalState,PosGlobalStateInherit);
//});