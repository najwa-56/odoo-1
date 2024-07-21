/** @odoo-module */

import { Component } from "@odoo/owl";
import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";
import { patch } from "@web/core/utils/patch";

ProductCard.props = {
    class: { type: String, optional: true },
    name: { type: String },
    productArabic: { type: String, optional: true },
    productId: { type: Number },
    price: { type: String },
    imageUrl: { type: String },
    productInfo: { type: Boolean, optional: true },
    onClick: { type: Function, optional: true },
    onProductInfoClick: { type: Function, optional: true },
};

// Example of passing props to ProductCard
const productProps = {
    class: 'product-card',
    name: 'Sample Product',
    productArabic: null, // Passing null for productArabic
    productId: 1,
    price: '10.00',
    imageUrl: 'path/to/image',
    productInfo: true,
    onClick: () => console.log('Product clicked'),
    onProductInfoClick: () => console.log('Product info clicked'),
};

// Using the ProductCard component with the productProps
<ProductCard {...productProps} />


