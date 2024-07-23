# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Global Search Document
    sh_global_document_search_is_enable = fields.Boolean(
        related='company_id.sh_global_document_search_is_enable', string='Enable global document search', readonly=False)
    sh_global_document_search_is_sale = fields.Boolean(
        related='company_id.sh_global_document_search_is_sale', string='Sale Order Search', readonly=False)
    sh_global_document_search_is_purchase = fields.Boolean(
        related='company_id.sh_global_document_search_is_purchase', string='Purchase Order Search', readonly=False)
    sh_global_document_search_is_picking = fields.Boolean(
        related='company_id.sh_global_document_search_is_picking', string='Picking Order Search', readonly=False)
    sh_global_document_search_is_invoice = fields.Boolean(
        related='company_id.sh_global_document_search_is_invoice', string='Invoice Order Search', readonly=False)
    sh_global_document_search_is_product = fields.Boolean(
        related='company_id.sh_global_document_search_is_product', string='Product Search', readonly=False)
    sh_global_document_search_is_lot = fields.Boolean(
        related='company_id.sh_global_document_search_is_lot', string='Lots/Serial Number Search', readonly=False)
    sh_global_document_search_is_location = fields.Boolean(
        related='company_id.sh_global_document_search_is_location', string='Location Search', readonly=False)
    sh_global_document_search_action_target_type = fields.Selection(
        related='company_id.sh_global_document_search_action_target_type', string='Document Open Mode', readonly=False)

    # sale
    sh_sale_barcode_scanner_type = fields.Selection(
        related='company_id.sh_sale_barcode_scanner_type', string='Product Scan Options (sale)', readonly=False)
    sh_sale_barcode_scanner_last_scanned_color = fields.Boolean(
        related='company_id.sh_sale_barcode_scanner_last_scanned_color', string='Last scanned Color? (sale)', readonly=False)
    sh_sale_barcode_scanner_move_to_top = fields.Boolean(
        related='company_id.sh_sale_barcode_scanner_move_to_top', string='Last scanned Move To Top? (sale)', readonly=False)
    sh_sale_barcode_scanner_warn_sound = fields.Boolean(
        related='company_id.sh_sale_barcode_scanner_warn_sound', string='Warning Sound? (sale)', readonly=False)
    sh_sale_barcode_scanner_auto_close_popup = fields.Integer(
        related='company_id.sh_sale_barcode_scanner_auto_close_popup', string='Auto close alert/error message after (sale)', readonly=False)

    # purchase
    sh_purchase_barcode_scanner_type = fields.Selection(
        related='company_id.sh_purchase_barcode_scanner_type', string='Product Scan Options (Purchase)', readonly=False)
    sh_purchase_barcode_scanner_last_scanned_color = fields.Boolean(
        related='company_id.sh_purchase_barcode_scanner_last_scanned_color', string='Last scanned Color? (Purchase)', readonly=False)
    sh_purchase_barcode_scanner_move_to_top = fields.Boolean(
        related='company_id.sh_purchase_barcode_scanner_move_to_top', string='Last scanned Move To Top? (Purchase)', readonly=False)
    sh_purchase_barcode_scanner_warn_sound = fields.Boolean(
        related='company_id.sh_purchase_barcode_scanner_warn_sound', string='Warning Sound? (Purchase)', readonly=False)
    sh_purchase_barcode_scanner_auto_close_popup = fields.Integer(
        related='company_id.sh_purchase_barcode_scanner_auto_close_popup', string='Auto close alert/error message after (Purchase)', readonly=False)

    # stock picking
    sh_inventory_barcode_scanner_type = fields.Selection(
        related='company_id.sh_inventory_barcode_scanner_type', string='Product Scan Options (Picking)', readonly=False)
    sh_inventory_barcode_scanner_is_add_product = fields.Boolean(
        related="company_id.sh_inventory_barcode_scanner_is_add_product", string="Is add new product in picking?", readonly=False)
    sh_inventory_barcode_scanner_last_scanned_color = fields.Boolean(
        related='company_id.sh_inventory_barcode_scanner_last_scanned_color', string='Last scanned Color? (Picking)', readonly=False)
    sh_inventory_barcode_scanner_move_to_top = fields.Boolean(
        related='company_id.sh_inventory_barcode_scanner_move_to_top', string='Last scanned Move To Top? (Picking)', readonly=False)
    sh_inventory_barcode_scanner_warn_sound = fields.Boolean(
        related='company_id.sh_inventory_barcode_scanner_warn_sound', string='Warning Sound? (Picking)', readonly=False)
    sh_inventory_barcode_scanner_auto_close_popup = fields.Integer(
        related='company_id.sh_inventory_barcode_scanner_auto_close_popup', string='Auto close alert/error message after (Picking)', readonly=False)

    # inventory adjustment
    sh_inven_adjt_barcode_scanner_type = fields.Selection(
        related='company_id.sh_inven_adjt_barcode_scanner_type', string='Product Scan Options (Inventory Adjustment)', readonly=False)
    sh_inven_adjt_barcode_scanner_warn_sound = fields.Boolean(
        string='Warning Sound? (Inventory Adjustment)', related='company_id.sh_inven_adjt_barcode_scanner_warn_sound', readonly=False)
    sh_inven_adjt_barcode_scanner_auto_close_popup = fields.Integer(
        related='company_id.sh_inven_adjt_barcode_scanner_auto_close_popup', string='Auto close alert/error message after (Inventory Adjustment)', readonly=False)

    # Scrap
    sh_scrap_barcode_scanner_type = fields.Selection(
        related='company_id.sh_scrap_barcode_scanner_type', string='Product Scan Options (Scrap)', readonly=False)
    sh_scrap_barcode_scanner_warn_sound = fields.Boolean(
        string='Warning Sound? (Scrap)', related='company_id.sh_scrap_barcode_scanner_warn_sound', readonly=False)
    sh_scrap_barcode_scanner_auto_close_popup = fields.Integer(
        related='company_id.sh_scrap_barcode_scanner_auto_close_popup', string='Auto close alert/error message after (Scrap)', readonly=False)

    # invoice
    sh_invoice_barcode_scanner_type = fields.Selection(
        related='company_id.sh_invoice_barcode_scanner_type', string='Product Scan Options (Invoice)', readonly=False)
    sh_invoice_barcode_scanner_last_scanned_color = fields.Boolean(
        related='company_id.sh_invoice_barcode_scanner_last_scanned_color', string='Last scanned Color? (Invoice)', readonly=False)
    sh_invoice_barcode_scanner_move_to_top = fields.Boolean(
        related='company_id.sh_invoice_barcode_scanner_move_to_top', string='Last scanned Move To Top? (Invoice)', readonly=False)
    sh_invoice_barcode_scanner_warn_sound = fields.Boolean(
        related='company_id.sh_invoice_barcode_scanner_warn_sound', string='Warning Sound? (Invoice)', readonly=False)
    sh_invoice_barcode_scanner_auto_close_popup = fields.Integer(
        related='company_id.sh_invoice_barcode_scanner_auto_close_popup', string='Auto close alert/error message after (Invoice)', readonly=False)

    # BOM
    sh_bom_barcode_scanner_type = fields.Selection(
        related='company_id.sh_bom_barcode_scanner_type', string='Product Scan Options (BOM)', readonly=False)
    sh_bom_barcode_scanner_last_scanned_color = fields.Boolean(
        related='company_id.sh_bom_barcode_scanner_last_scanned_color', string='Last scanned Color? (BOM)', readonly=False)
    sh_bom_barcode_scanner_move_to_top = fields.Boolean(
        related='company_id.sh_bom_barcode_scanner_move_to_top', string='Last scanned Move To Top? (BOM)', readonly=False)
    sh_bom_barcode_scanner_warn_sound = fields.Boolean(
        related='company_id.sh_bom_barcode_scanner_warn_sound', string='Warning Sound? (BOM)', readonly=False)
    sh_bom_barcode_scanner_auto_close_popup = fields.Integer(
        related='company_id.sh_bom_barcode_scanner_auto_close_popup', string='Auto close alert/error message after (BOM)', readonly=False)
