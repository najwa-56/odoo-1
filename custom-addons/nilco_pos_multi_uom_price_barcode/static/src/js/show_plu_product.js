/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ProductsWidget } from "@point_of_sale/app/screens/product_screen/product_list/product_list";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";

patch(ProductsWidget.prototype, {
    setup() {
        super.setup();
        this.pos=usePos();
    },
        get productsToDisplay() {
        let list = [];
        if (this.searchWord !== '') {
                list = this.pos.db.bi_search_product_in_category(
                    this.selectedCategoryId,
                    this.searchWord
                );
            
        } else {
            list = this.pos.db.get_product_by_category(this.selectedCategoryId);
        }
        return list.sort(function (a, b) { return a.display_name.localeCompare(b.display_name) });
    }
});
