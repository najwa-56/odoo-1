# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # Global Search Document
    sh_global_document_search_is_enable = fields.Boolean(
        string='Enable global document search')
    sh_global_document_search_is_sale = fields.Boolean(
        string='Sale Order Search')
    sh_global_document_search_is_purchase = fields.Boolean(
        string='Purchase Order Search')
    sh_global_document_search_is_picking = fields.Boolean(
        string='Picking Order Search')
    sh_global_document_search_is_invoice = fields.Boolean(
        string='Invoice Order Search')
    sh_global_document_search_is_product = fields.Boolean(
        string='Product Search')
    sh_global_document_search_is_lot = fields.Boolean(
        string='Lots/Serial Number Search')
    sh_global_document_search_is_location = fields.Boolean(
        string='Location Search')
    sh_global_document_search_action_target_type = fields.Selection(
        [('current', 'Current'), ('new', 'New')], default='current', string='Document Open Mode')

    # sale
    sh_sale_barcode_scanner_type = fields.Selection([('int_ref', 'Internal Reference'),
                                                     ('barcode', 'Barcode'),
                                                     ('sh_qr_code', 'QR Code'),
                                                     ('all', 'All'),], default='barcode', string='Product Scan Options (sale)')

    sh_sale_barcode_scanner_last_scanned_color = fields.Boolean(
        string='Last scanned Color? (sale)')
    sh_sale_barcode_scanner_move_to_top = fields.Boolean(
        string='Last scanned Move To Top? (sale)')
    sh_sale_barcode_scanner_warn_sound = fields.Boolean(
        string='Warning Sound? (sale)')
    sh_sale_barcode_scanner_auto_close_popup = fields.Integer(
        string='Auto close alert/error message after (sale)')

    # purchase
    sh_purchase_barcode_scanner_type = fields.Selection([('int_ref', 'Internal Reference'),
                                                         ('barcode', 'Barcode'),
                                                         ('sh_qr_code', 'QR Code'),
                                                         ('all', 'All'),], default='barcode', string='Product Scan Options (Purchase)')
    sh_purchase_barcode_scanner_last_scanned_color = fields.Boolean(
        string='Last scanned Color? (Purchase)')
    sh_purchase_barcode_scanner_move_to_top = fields.Boolean(
        string='Last scanned Move To Top? (Purchase)')
    sh_purchase_barcode_scanner_warn_sound = fields.Boolean(
        string='Warning Sound? (Purchase)')
    sh_purchase_barcode_scanner_auto_close_popup = fields.Integer(
        string='Auto close alert/error message after (Purchase)')

    # stock picking
    sh_inventory_barcode_scanner_type = fields.Selection([('int_ref', 'Internal Reference'),
                                                          ('barcode', 'Barcode'),
                                                          ('sh_qr_code',
                                                           'QR Code'),
                                                          ('all', 'All'),], default='barcode', string='Product Scan Options (Picking)')
    sh_inventory_barcode_scanner_is_add_product = fields.Boolean(
        string="Is add new product in picking?")
    sh_inventory_barcode_scanner_last_scanned_color = fields.Boolean(
        string='Last scanned Color? (Picking)')
    sh_inventory_barcode_scanner_move_to_top = fields.Boolean(
        string='Last scanned Move To Top? (Picking)')
    sh_inventory_barcode_scanner_warn_sound = fields.Boolean(
        string='Warning Sound? (Picking)')
    sh_inventory_barcode_scanner_auto_close_popup = fields.Integer(
        string='Auto close alert/error message after (Picking)')

    # inventory adjustment
    sh_inven_adjt_barcode_scanner_type = fields.Selection([('int_ref', 'Internal Reference'),
                                                           ('barcode', 'Barcode'),
                                                           ('sh_qr_code',
                                                            'QR Code'),
                                                           ('all', 'All'),], default='barcode', string='Product Scan Options (Inventory Adjustment)')
    sh_inven_adjt_barcode_scanner_warn_sound = fields.Boolean(
        string='Warning Sound? (Inventory Adjustment)')
    sh_inven_adjt_barcode_scanner_auto_close_popup = fields.Integer(
        string='Auto close alert/error message after (Inventory Adjustment)')

    # Scrap
    sh_scrap_barcode_scanner_type = fields.Selection([('int_ref', 'Internal Reference'),
                                                      ('barcode', 'Barcode'),
                                                      ('sh_qr_code', 'QR Code'),
                                                      ('all', 'All'),], default='barcode', string='Product Scan Options (Scrap)')
    sh_scrap_barcode_scanner_warn_sound = fields.Boolean(
        string='Warning Sound? (Scrap)', readonly=False)
    sh_scrap_barcode_scanner_auto_close_popup = fields.Integer(
        string='Auto close alert/error message after (Scrap)', readonly=False)

    # invoice
    sh_invoice_barcode_scanner_type = fields.Selection([('int_ref', 'Internal Reference'),
                                                        ('barcode', 'Barcode'),
                                                        ('sh_qr_code', 'QR Code'),
                                                        ('all', 'All'),], default='barcode', string='Product Scan Options (Invoice)')
    sh_invoice_barcode_scanner_last_scanned_color = fields.Boolean(
        string='Last scanned Color? (Invoice)', readonly=False)
    sh_invoice_barcode_scanner_move_to_top = fields.Boolean(
        string='Last scanned Move To Top? (Invoice)', readonly=False)
    sh_invoice_barcode_scanner_warn_sound = fields.Boolean(
        string='Warning Sound? (Invoice)', readonly=False)
    sh_invoice_barcode_scanner_auto_close_popup = fields.Integer(
        string='Auto close alert/error message after (Invoice)', readonly=False)

    # BOM
    sh_bom_barcode_scanner_type = fields.Selection([('int_ref', 'Internal Reference'),
                                                    ('barcode', 'Barcode'),
                                                    ('sh_qr_code', 'QR Code'),
                                                    ('all', 'All'),], default='barcode', string='Product Scan Options (BOM)')
    sh_bom_barcode_scanner_last_scanned_color = fields.Boolean(
        string='Last scanned Color? (BOM)')
    sh_bom_barcode_scanner_move_to_top = fields.Boolean(
        string='Last scanned Move To Top? (BOM)')
    sh_bom_barcode_scanner_warn_sound = fields.Boolean(
        string='Warning Sound? (BOM)')
    sh_bom_barcode_scanner_auto_close_popup = fields.Integer(
        string='Auto close alert/error message after (BOM)')
