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
    productArabic: String,
    productId: Number,
    price: String,
    imageUrl: String,
    productInfo: { Boolean, optional: true },
    onClick: { type: Function, optional: true },
    onProductInfoClick: { type: Function, optional: true },
};

// Ensure productArabic is a string
const products = [
    // Example product object
    { name: "Product 1", productArabic: "منتج 1", productId: 1, price: "10.00", imageUrl: "image1.jpg", productInfo: true },
    // Example with productArabic potentially being null or undefined
    { name: "Product 2", productArabic: null, productId: 2, price: "20.00", imageUrl: "image2.jpg", productInfo: true },
];

products.forEach(product => {
    // Ensure productArabic is a string, default to empty string if null or undefined
    const productArabic = product.productArabic ? String(product.productArabic) : '';

    // Render or pass to the ProductCard component
    <ProductCard
        class={product.class}
        name={product.name}
        productArabic={productArabic}
        productId={product.productId}
        price={product.price}
        imageUrl={product.imageUrl}
        productInfo={product.productInfo}
        onClick={product.onClick}
        onProductInfoClick={product.onProductInfoClick}
    />
});



