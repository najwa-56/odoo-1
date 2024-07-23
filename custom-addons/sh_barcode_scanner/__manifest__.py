# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
{
    "name": "All In One Barcode Scanner-Basic",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "version": "0.0.2",
    "category": "Extra Tools",
    "summary": "Barcode Scanner Package Sales Barcode Scanner Purchase Barcode Scanner Account Barcode Scanner Stock Barcode Scanner BOM Barcode Scanner Request For Quotation Barcode Scanner Bill Barcode Scanner PO Barcode Scanner RFQ Barcode Scanner Add Product on Sales by barcode scanner all barcode sale barcode purchase barcode invoice barcode bom barcode inventory barcode Scan product by Barcode Scanner scan barcode on purchase scan barcode on invoice scan barcode on sale order barcode report All in one mobile barcode QR code scanner barcode and qr code scanner widget mobile barcode mobile qr code mobile qrcode barcode scanner qr code scanner mobile qrcode scanner mobile barcode scanner mobile qrcode scanner Odoo Sale Order Barcode Scanner Purchase Order Barcode Scanner Invoice Barcode Scanner Inventory Barcode Scanner Bill Of Material Barcode Scanner Scrap Barcode Scanner Warehouse Barcode Scanner",
    "description": """Do your time-wasting in sales, purchases, invoices, inventory, bill of material, scrap operations by manual product selection? So here are the solutions these modules useful do quick operations of sales, purchases, invoicing and inventory, bill of material, scrap using barcode scanner. You no need to select the product and do one by one. scan it and you do! So be very quick in all operations of odoo and cheers!

 All In One Barcode Scanner - Sales, Purchase, Invoice, Inventory, BOM, Scrap Odoo.
Operations Of Sales, Purchase Using Barcode, Invoice Using Barcode, Inventory Using Barcode, Bill Of Material Using Barcode, Scrap Using Barcode Module, Sales Barcode Scanner,Purchase Barcode Scanner, Invoice Barcode Scanner, Inventory Barcode Scanner,Bom Barcode Scanner, Single Product Multi Barcode Odoo.
 
 Barcode Scanner App,Package All in one barcode scanner,  Operations Of Sales, Purchase In Barcode Module, Invoice In Barcode, Inventory In Barcode, Bom In Barcode, Scrap Using Barcode, Single Product Multi Barcode, Sales Barcode Scanner,Purchase Barcode Scanner, Invoice Barcode Scanner, Inventory Barcode Scanner,Bom Barcode Scanner, Single Product Multi Barcode Odoo.


Add products by barcode    
Add products using barcode    

sales mobile barcode scanner
so barcode scanner
so mobile barcode scanner
sale mobile barcode scanner

po mobile barcode scanner
purchase order mobile barcode scanner
purchase order barcode scanner
po barcode scanner
    
inventory mobile barcode scanner    
stock mobile barcode scanner
inventory barcode scanner
stock barcode scanner

inventory adjustment mobile barcode scanner
stock adjustment mobile barcode scanner
inventory adjustment barcode scanner
stock adjustment barcode scanner

invoice barcode scanner
bill barcode scanner
credit note barcode scanner
debit note barcode scanner
invoice barcode mobile scanner
bill barcode mobile scanner
credit note barcode mobile scanner
debit note barcode mobile scanner

     """,
    "depends": [
                "purchase",
                "sale_management",
                "barcodes",
                "account",
                "stock",
                "mrp",
                "sh_product_qrcode_generator",
    ],
    "data": [
        "security/ir.model.access.csv",

        # Account
        "views/account/account_move_views.xml",
        "views/account/res_config_settings_views.xml",

        # Global Search
        "views/global_doc_search/res_config_settings_views.xml",
        "views/global_doc_search/stock_location_views.xml",

        # Manufacturing
        "views/mrp_bom/mrp_bom_views.xml",
        "views/mrp_bom/res_config_settings_views.xml",

        # Product
        "views/product/product_views.xml",

        # Purchase
        "views/purchase/purchase_order_views.xml",
        "views/purchase/res_config_settings_views.xml",

        # Sale
        "views/sale/sale_order_views.xml",
        "views/sale/res_config_settings_views.xml",

        # Stock Adjustment
        "views/stock_inventory/res_config_settings_views.xml",
        "views/stock_inventory/stock_quant_views.xml",

        # Stock Move
        "views/stock_move/stock_move_views.xml",

        # Stock Picking
        "views/stock_picking/res_config_settings_views.xml",
        "views/stock_picking/stock_move_line_views.xml",
        "views/stock_picking/stock_move_views.xml",
        "views/stock_picking/stock_picking_views.xml",

        # Stock Scarp
        "views/stock_scrap/res_config_settings_views.xml",
        "views/stock_scrap/stock_scrap_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "sh_barcode_scanner/static/src/**/*",
        ],
    },
    "images": ["static/description/background.png", ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "price": 35,
    "currency": "EUR",
    "license": "OPL-1",
}
