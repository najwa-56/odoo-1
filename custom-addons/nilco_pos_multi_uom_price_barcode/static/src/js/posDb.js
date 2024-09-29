/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosDB } from "@point_of_sale/app/store/db";
import { unaccent } from "@web/core/utils/strings";
import { jsonrpc } from "@web/core/network/rpc_service";


patch(PosDB.prototype, {


   

    bi_search_product_in_category(category_id, query) {
        try {
            // eslint-disable-next-line no-useless-escape
            query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g, ".");
            query = query.replace(/ /g, ".+");
            var re = RegExp("([0-9]+):.*?" + unaccent(query), "gi");
        } catch {
            return [];
        }
        var results = [];
        for (var i = 0; i < this.limit; i++) {
            var r = re.exec(this.category_search_string[category_id]);
            if (r) {
                var id = Number(r[1]);
                const product = this.get_product_by_id(id);
                if (!this.shouldAddProduct(product, results)) {
                    continue;
                }
                results.push(product);
            } else {
                break;
            }
        }
        return results;
    },
    bi_product_search_string(product) {
        var str = product.display_name;
        if (product.barcode) {
            str += "|" + product.barcode;
        }
        if (product.default_code) {
            str += "|" + product.default_code;
        }
        if (product.description) {
            str += "|" + product.description;
        }
        if (product.description_sale) {
            str += "|" + product.description_sale;
        }
         // Include the new_barcode field (which is a JSON string of barcodes)
    if (product.new_barcode) {
        const barcodes = JSON.parse(product.new_barcode);
        barcodes.forEach(function (barcode) {
            str += "|" + barcode;
        });
    }
        str = product.id + ":" + str.replace(/[\n:]/g, "") + "\n";
        return str;
    }
});