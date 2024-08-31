import { Component } from "@odoo/owl";
import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";
import { patch } from "@web/core/utils/patch";

// Patch the ProductCard to define new props or modify existing ones
patch(ProductCard.prototype, "product-card-patch", {
    setup() {
        // Always call the super setup if you're extending the setup method
        super.setup();
    },
});

// Define or redefine props for the ProductCard component
ProductCard.props = {
    class: { type: String, optional: true },
    name: { type: String },
    productArabic: { type: String }, // Ensuring type is explicitly defined
    productId: { type: Number },
    price: { type: String },
    imageUrl: { type: String },
    productInfo: { type: Boolean, optional: true },
    onClick: { type: Function, optional: true },
    onProductInfoClick: { type: Function, optional: true },
};


