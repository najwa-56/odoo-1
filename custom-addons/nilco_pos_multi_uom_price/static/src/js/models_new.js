/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { Order} from "@point_of_sale/app/store/models";

patch(Order.prototype, {
    set_pricelist(pricelist) {
        super.setup(...arguments);
        var self = this;
        this.pricelist = pricelist;

        const orderlines = this.get_orderlines();
        if (!this.get_orderlines) {
    console.error('get_orderlines method is not available on Order instance.');
    return;
}console.log('Order instance:', this);
console.log('Pricelist:', pricelist);
console.log('Orderlines:', this.get_orderlines());

        const lines_to_recompute = orderlines.filter(
            (line) =>
                line.price_type === "original" && !(line.comboLines?.length || line.comboParent)
        );
        const combo_parent_lines = orderlines.filter(
            (line) => line.price_type === "original" && line.comboLines?.length
        );
        const attributes_prices = {};
        combo_parent_lines.forEach((parentLine) => {
            attributes_prices[parentLine.id] = this.compute_child_lines(
                parentLine.product,
                parentLine.comboLines.map((childLine) => {
                    const comboLineCopy = { ...childLine.comboLine };
                    if (childLine.attribute_value_ids) {
                        comboLineCopy.configuration = {
                            attribute_value_ids: childLine.attribute_value_ids,
                        };
                    }
                    return comboLineCopy;
                }),
                pricelist
            );
        });
        const combo_children_lines = orderlines.filter(
            (line) => line.price_type === "original" && line.comboParent
        ); 
    },
});
