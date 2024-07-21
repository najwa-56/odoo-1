/** @odoo-module */

import { Component } from "@odoo/owl";
import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";
import { patch } from "@web/core/utils/patch";

//Patched the ProductCard for defining that clickMagnifyProduct is function
patch(ProductCard.prototype, {
    //Supering setup() function
    setup() {
        super.setup();
    },
});

ProductCard.props = {
    class: { type: String, optional: true },
    name: { type: String },
    productArabic: { type: String },
    productId: { type: Number },
    price: { type: String },
    imageUrl: { type: String },
    productInfo: { type: Boolean, optional: true },
    onClick: { type: Function, optional: true },
    onProductInfoClick: { type: Function, optional: true },
};



