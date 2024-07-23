# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies Pvt. Ltd.


from odoo import Command, _, models
from odoo.exceptions import UserError


class ShAccountMove(models.Model):
    _name = "account.move"
    _inherit = ["barcodes.barcode_events_mixin", "account.move"]

    def on_barcode_scanned(self, barcode):
        """
            Override By Softhealer Technologies Pvt. Ltd.
        The function is used to handle barcode scanning in an invoice, updating the
        quantity of a product or creating a new order line if the product is not already in the invoice.

        :param barcode: The barcode parameter is the scanned barcode value. It is used to search for the
        corresponding product in the invoice line items
        """
        company_sudo = self.env.company.sudo()
        is_last_scanned = False
        sequence = 0
        warn_sound_code = ""

        if company_sudo.sh_invoice_barcode_scanner_last_scanned_color:
            is_last_scanned = True

        if company_sudo.sh_invoice_barcode_scanner_move_to_top:
            sequence = -1

        if company_sudo.sh_invoice_barcode_scanner_warn_sound:
            warn_sound_code = "SH_BARCODE_SCANNER_"

        if company_sudo.sh_invoice_barcode_scanner_auto_close_popup:
            warn_sound_code += "AUTO_CLOSE_AFTER_" + \
                str(self.env.user.company_id.sudo(
                ).sh_invoice_barcode_scanner_auto_close_popup) + "_MS&"

        # step 1 increase product qty by 1 if product not in order line than create new order line.
        if self and self.state == "draft":
            self.invoice_line_ids.with_context(check_move_validity=False).update(
                {'sh_invoice_barcode_scanner_is_last_scanned': False, 'sequence': 0})
            search_lines = False
            domain = []
            if company_sudo.sh_invoice_barcode_scanner_type == "barcode":
                search_lines = self.invoice_line_ids.filtered(
                    lambda ol: ol.product_id.barcode == barcode)
                domain = [("barcode", "=", barcode)]

            elif company_sudo.sh_invoice_barcode_scanner_type == "int_ref":
                search_lines = self.invoice_line_ids.filtered(
                    lambda ol: ol.product_id.default_code == barcode)
                domain = [("default_code", "=", barcode)]

            elif company_sudo.sh_invoice_barcode_scanner_type == "sh_qr_code":
                search_lines = self.invoice_line_ids.filtered(
                    lambda ol: ol.product_id.sh_qr_code == barcode)
                domain = [("sh_qr_code", "=", barcode)]

            elif company_sudo.sh_invoice_barcode_scanner_type == "all":
                search_lines = self.invoice_line_ids.filtered(lambda ol: barcode in (
                    ol.product_id.barcode, ol.product_id.default_code, ol.product_id.sh_qr_code))

                domain = ["|", "|", ("default_code", "=", barcode),
                          ("barcode", "=", barcode),
                          ("sh_qr_code", "=", barcode)]

            if search_lines:
                # PICK LAST LINE IF MULTIPLE LINE FOUND
                search_lines = search_lines[-1]
                search_lines.quantity += 1
                search_lines.sh_invoice_barcode_scanner_is_last_scanned = is_last_scanned
                search_lines.sequence = sequence
            else:
                search_product = self.env["product.product"].search(
                    domain, limit=1)
                if search_product:
                    self.invoice_line_ids = [Command.create({'product_id': search_product.id,
                                                             'sh_invoice_barcode_scanner_is_last_scanned': is_last_scanned,
                                                             'sequence': sequence})]
                else:
                    raise UserError(
                        _(warn_sound_code + "Scanned Internal Reference/Barcode/QR Code '%s' does not exist in any product!") % (barcode))

        else:
            selections = self.fields_get()["state"]["selection"]
            value = next((v[1] for v in selections if v[0]
                         == self.state), self.state)
            raise UserError(
                _(warn_sound_code + "You can not scan item in %s state.") % (value))
