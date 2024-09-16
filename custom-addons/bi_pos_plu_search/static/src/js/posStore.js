/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { _t } from "@web/core/l10n/translation";
import { PosCollection, Order, Product } from "@point_of_sale/app/store/models";

patch(PosStore.prototype, {

    async _processData(loadedData) {
        await super._processData(...arguments);
        let self = this;
        this._loadProductProduct(loadedData['product.product']);
    },
    _loadProductProduct(products) {
        const productMap = {};
        const productTemplateMap = {};

        const modelProducts = products.map((product) => {
            product.pos = this;
            product.env = this.env;
            product.applicablePricelistItems = {};
            productMap[product.id] = product;
            productTemplateMap[product.product_tmpl_id[0]] = (
                productTemplateMap[product.product_tmpl_id[0]] || []
            ).concat(product);
            return new Product(product);
        });

        for (const pricelist of this.pricelists) {
            for (const pricelistItem of pricelist.items) {
                if (pricelistItem.product_id) {
                    const product_id = pricelistItem.product_id[0];
                    const correspondingProduct = productMap[product_id];
                    if (correspondingProduct) {
                        this._assignApplicableItems(pricelist, correspondingProduct, pricelistItem);
                    }
                } else if (pricelistItem.product_tmpl_id) {
                    const product_tmpl_id = pricelistItem.product_tmpl_id[0];
                    const correspondingProducts = productTemplateMap[product_tmpl_id];
                    for (const correspondingProduct of correspondingProducts || []) {
                        this._assignApplicableItems(pricelist, correspondingProduct, pricelistItem);
                    }
                } else {
                    for (const correspondingProduct of products) {
                        this._assignApplicableItems(pricelist, correspondingProduct, pricelistItem);
                    }
                }
            }
        }
        if (this.config.allow_plu_search){
                this.db.bi_add_products(modelProducts)
        }else{
            this.db.add_products(modelProducts)
        }
    }
});
