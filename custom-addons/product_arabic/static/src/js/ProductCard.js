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
        class: { String, optional: true },
        name: String,
        productArabic: {type: String, optional: true },
        productId: Number,
        price: String,
        imageUrl: String,
        productInfo: { Boolean, optional: true },
        onClick: { type: Function, optional: true },
        onProductInfoClick: { type: Function, optional: true },
};

const productCardInstance = new ProductCard({
    props: {
        class: "some-class",
        name: "Sample Product",
        productArabic: "undefined",  // Set as an empty string
        productId: 1,
        price: "10.00",
        imageUrl: "/path/to/image",
        productInfo: true,
        onClick: () => { /* some function */ },
        onProductInfoClick: () => { /* some function */ },
    },
});




