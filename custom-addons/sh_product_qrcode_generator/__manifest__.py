# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
{
    "name": "Product QR Code Generator",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "version": "0.0.1",
    "category": "Extra Tools",
    "license": "OPL-1",
    "summary": "Default Make QR Module New Product QR Generate App Existing Product QR Generate Application Existing Multi Product QR Create Custom Product QR Generator Product QRCode Generator QRCode Product Odoo Print QRCode In Product Labels Print QR Code In Product Labels Products QRCode Generator Unique QR Code Generator Unique QRCode Generator Product Variants QRCode Generator Product Variants QR Code Generator Generate QR Code Odoo Automatic Generate Product QR Odoo Generate Product QR Codes Product QR Code Creator QR Code Generator for Products Create QR Codes for Products Quick Response code Item QR Code Creator QR Code Label Maker for Products Generate QR Codes for Inventory Items Product Identification QR Codes QR Code Printing for Products Product Label QR Code Generator Create Unique QR Codes for Products",
    "description": """This module automatically generates QR Code for the Product. It allows for generating QR Code for existing products. Generate QR Code on new product creation. This module helps to set up a unique QR Code for products. This module provides functionality to generate product QR Code If already exists.
 Automatic Generate Product QR Odoo
 By Default Make QR Module, Auto Generate New Product QR, Automatic Generate Existing Product QR, Auto Create Existing Multi Product QR, Custom Product QR Generator Odoo.""",
    "depends": [
            "product",
            "base_setup"
    ],
    "images": ["static/description/background.png", ],
    "data": [
        "data/ir_sequence_data.xml",
        "security/sh_product_qr_code_groups.xml",
        "security/ir.model.access.csv",

        "views/res_config_settings_views.xml",
        "views/product_product_views.xml",
        "views/product_template_views.xml",

        "report/product_product_templates.xml",
        "report/product_template_templates.xml",
        "report/product_report.xml",

        "wizard/sh_product_qrcode_generator_label_layout_wizard_views.xml",
        "wizard/sh_qr_generator_views.xml",

    ],
    "external_dependencies": {
        "python": ["qrcode"],
    },
    "installable": True,
    "auto_install": False,
    "application": True,
    "price": 12,
    "currency": "EUR",
}
