# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import _, models,Command
from odoo.exceptions import UserError


class ShMrpBom(models.Model):
    _name = "mrp.bom"
    _inherit = ["barcodes.barcode_events_mixin", "mrp.bom"]

    def on_barcode_scanned(self, barcode):
        is_last_scanned = False
        sequence = 0
        warm_sound_code = ""

        if self.env.user.company_id.sudo().sh_bom_barcode_scanner_last_scanned_color:
            is_last_scanned = True

        if self.env.user.company_id.sudo().sh_bom_barcode_scanner_move_to_top:
            sequence = -1

        if self.env.user.company_id.sudo().sh_bom_barcode_scanner_warn_sound:
            warm_sound_code = "SH_BARCODE_SCANNER_"

        if self.env.user.company_id.sudo().sh_bom_barcode_scanner_auto_close_popup:
            warm_sound_code += "AUTO_CLOSE_AFTER_" + \
                str(self.env.user.company_id.sudo().sh_bom_barcode_scanner_auto_close_popup) + "_MS&"

        # step 2 increase product qty by 1 if product not in bom line than create new bom line.
        if self:
            self.bom_line_ids.update({'sh_bom_barcode_scanner_is_last_scanned': False,'sequence': 0})

            search_lines = False
            domain = []
            if self.env.user.company_id.sudo().sh_bom_barcode_scanner_type == "barcode":
                search_lines = self.bom_line_ids.filtered(lambda ol: ol.product_id.barcode == barcode)
                domain = [("barcode", "=", barcode)]

            elif self.env.user.company_id.sudo().sh_bom_barcode_scanner_type == "int_ref":
                search_lines = self.bom_line_ids.filtered(lambda ol: ol.product_id.default_code == barcode)
                domain = [("default_code", "=", barcode)]

            elif self.env.user.company_id.sudo().sh_bom_barcode_scanner_type == "sh_qr_code":
                search_lines = self.bom_line_ids.filtered(lambda ol: ol.product_id.sh_qr_code == barcode)
                domain = [("sh_qr_code", "=", barcode)]

            elif self.env.user.company_id.sudo().sh_bom_barcode_scanner_type == "all":
                search_lines = self.bom_line_ids.filtered(lambda ol: barcode in (ol.product_id.barcode, ol.product_id.default_code, ol.product_id.sh_qr_code))

                domain = ["|", "|", ("default_code", "=", barcode), ("barcode", "=", barcode), ("sh_qr_code", "=", barcode)]

            if search_lines:
                for line in search_lines:
                    line.product_qty += 1
                    line.sh_bom_barcode_scanner_is_last_scanned = is_last_scanned
                    line.sequence = sequence
                    break
            else:
                search_product = self.env["product.product"].search(domain, limit=1)
                if search_product:
                    bom_line_vals = {"product_id": search_product.id,"product_qty": 1,'sh_bom_barcode_scanner_is_last_scanned': is_last_scanned,'sequence': sequence}

                    if search_product.uom_id:
                        bom_line_vals.update({"product_uom_id": search_product.uom_id.id})

                    self.bom_line_ids = [Command.create(bom_line_vals)]
                else:
                    raise UserError(_(warm_sound_code + "Scanned Internal Reference/Barcode/QR Code '%s' does not exist in any product!") % (barcode))
