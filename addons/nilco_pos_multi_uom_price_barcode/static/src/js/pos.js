/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosDB } from "@point_of_sale/app/store/db";
import { unaccent } from "@web/core/utils/strings";
import { jsonrpc } from "@web/core/network/rpc_service";

patch(PosDB.prototype, {
    add_products(products) {
        var stored_categories = this.product_by_category_id;
        if (!(products instanceof Array)) {
            products = [products];
        }

        let product_ids = [];
        for (var i = 0, len = products.length; i < len; i++) {
            var product = products[i];
            if (product.id in this.product_by_id) {
                continue;
            }
            if (product.available_in_pos) {
                var search_string = unaccent(this.bi_product_search_string(product));
                const all_categ_ids = product.pos_categ_ids.length
                    ? product.pos_categ_ids
                    : [this.root_category_id];
                product.product_tmpl_id = product.product_tmpl_id[0];
                for (const categ_id of all_categ_ids) {
                    if (!stored_categories[categ_id]) {
                        stored_categories[categ_id] = [];
                    }
                    stored_categories[categ_id].push(product.id);
                    if (this.category_search_string[categ_id] === undefined) {
                        this.category_search_string[categ_id] = "";
                    }
                    this.category_search_string[categ_id] += search_string;
                    var ancestors = this.get_category_ancestors_ids(categ_id) || [];
                    for (var j = 0, jlen = ancestors.length; j < jlen; j++) {
                        var ancestor = ancestors[j];
                        if (!stored_categories[ancestor]) {
                            stored_categories[ancestor] = [];
                        }
                        stored_categories[ancestor].push(product.id);

                        if (this.category_search_string[ancestor] === undefined) {
                            this.category_search_string[ancestor] = "";
                        }
                        this.category_search_string[ancestor] += search_string;
                    }
                }
            }
            this.product_by_id[product.id] = product;
            product_ids.push(product.id);
        }

        // Make a single RPC call for all product_ids
        if (product_ids.length > 0) {
            var self = this;
            jsonrpc('/web/dataset/call_kw/product.product/get_barcode_val_batch', {
                model: 'product.product',
                method: 'get_barcode_val_batch',  // Call the new batch method
                args: [product_ids,product_ids],  // Pass the product IDs
                kwargs: {},
            }).then(function(barcode_vals) {
                // Assign barcodes to products in one step
                for (const [barcode, product_id] of barcode_vals) {
                    
                    if (product_id in self.product_by_id) {
                        self.product_by_barcode[barcode] = self.product_by_id[product_id];
                    }
                }
            }).catch(function(error) {
                console.error('Error fetching barcode values:', error);
            });
        }

        return super.add_products(products);
    },



    
});


