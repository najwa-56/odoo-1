# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import _, fields, models
from odoo.exceptions import UserError


class ShStockMove(models.Model):
    _name = "stock.move"
    _inherit = ['barcodes.barcode_events_mixin', 'stock.move']

    sequence = fields.Integer(default=1)
    sh_inventory_barcode_scanner_is_last_scanned = fields.Boolean(
        string="Last Scanned?")

    def on_barcode_scanned(self, barcode):
        """
            Override By Softhealer Technologies Pvt. Ltd.
        The function handles the scanning of barcodes and performs various checks
        and actions based on the barcode and the current state of the picking.

        :param barcode: The barcode parameter is the barcode that was scanned by the barcode scanner. It
        is used to identify the product that was scanned
        :return: The code does not explicitly return anything.
        """
        company_sudo = self.env.company.sudo()
        is_last_scanned = False
        sequence = 1
        warn_sound_code = ""

        if company_sudo.sh_inventory_barcode_scanner_last_scanned_color:
            is_last_scanned = True

        if company_sudo.sh_inventory_barcode_scanner_move_to_top:
            sequence = -1

        if company_sudo.sh_inventory_barcode_scanner_warn_sound:
            warn_sound_code = "SH_BARCODE_SCANNER_"

        if company_sudo.sh_inventory_barcode_scanner_auto_close_popup:
            warn_sound_code += "AUTO_CLOSE_AFTER_" + \
                str(company_sudo.sh_inventory_barcode_scanner_auto_close_popup) + "_MS&"
        move_lines = self.move_line_ids

        if self.picking_id.state not in ['confirmed', 'assigned']:
            selections = self.picking_id.fields_get()['state']['selection']
            value = next((v[1] for v in selections if v[0] ==
                         self.picking_id.state), self.picking_id.state)
            raise UserError(
                _(warn_sound_code + "You can not scan item in %s state.") % (value))

        elif move_lines:
            similar_lines = False
            barcode_match = False
            if company_sudo.sh_inventory_barcode_scanner_type == 'barcode':
                if self.product_id.barcode == barcode:
                    barcode_match = True
                    similar_lines = move_lines.filtered(
                        lambda ml: ml.product_id.barcode == barcode)
            elif company_sudo.sh_inventory_barcode_scanner_type == 'int_ref':
                if self.product_id.default_code == barcode:
                    barcode_match = True
                    similar_lines = move_lines.filtered(
                        lambda ml: ml.product_id.default_code == barcode)
            elif company_sudo.sh_inventory_barcode_scanner_type == 'sh_qr_code':
                if self.product_id.sh_qr_code == barcode:
                    barcode_match = True
                    similar_lines = move_lines.filtered(
                        lambda ml: ml.product_id.sh_qr_code == barcode)
            elif company_sudo.sh_inventory_barcode_scanner_type == 'all':
                if barcode in (self.product_id.barcode, self.product_id.default_code, self.product_id.sh_qr_code):
                    barcode_match = True
                    similar_lines = move_lines.filtered(lambda ml: barcode in (
                        ml.product_id.barcode, ml.product_id.default_code, ml.product_id.sh_qr_code))
            if not barcode_match:
                raise UserError(
                    _(warn_sound_code + "Scanned Internal Reference/Barcode/QR Code '%s' does not exist in any product!") % (barcode))

            if bool(similar_lines):
                len_similar_lines = len(similar_lines)
                if len_similar_lines:
                    last_line = similar_lines[len_similar_lines - 1]
                    last_line.quantity += 1
                    last_line._onchange_quantity()
                self.update({
                    "sequence": sequence,
                    "sh_inventory_barcode_scanner_is_last_scanned": is_last_scanned
                })

                if self.quantity == self.product_uom_qty + 1:
                    return {'warning': {'title': _('Alert!'), 'message': warn_sound_code + 'Becareful! Quantity exceed than initial demand!'}}
        else:
            raise UserError(
                _(warn_sound_code + "Pls add all product items in line than rescan."))
