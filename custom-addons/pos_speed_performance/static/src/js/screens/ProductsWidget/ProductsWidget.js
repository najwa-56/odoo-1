//odoo.define('pos_speed_performance.ProductsWidget', function (require) {
//    "use strict";
//
//    const models = require('point_of_sale.models');
//    const ProductsWidget = require('point_of_sale.ProductsWidget');
//    const Registries = require('point_of_sale.Registries');
//
//
//    let ProductsWidgetSearchOnline = ProductsWidget =>
//        class extends ProductsWidget {
//            async _updateSearch(event) {
//                super._updateSearch(event);
//                const searchResults = this.productsToDisplay;
//                if (searchResults.length === 0){
//                    try {
//                        let search_string = event.detail;
//                        await this.env.pos.search_product_to_server(search_string);
//                        this.render(true);
//                    } catch (error) {
//                        if (error == undefined) {
//                            await this.showPopup('OfflineErrorPopup', {
//                                title: this.env._t('Offline'),
//                                body: this.env._t('Unable to search customer.'),
//                            });
//                        }
//                    }
//                }
//
//            }
//        }
//    Registries.Component.extend(ProductsWidget, ProductsWidgetSearchOnline);
//
//    return ProductsWidget;
//
//});