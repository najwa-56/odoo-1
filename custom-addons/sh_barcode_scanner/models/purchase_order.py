# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression


class ShPurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ["barcodes.barcode_events_mixin", "purchase.order"]

    def on_barcode_scanned(self, barcode):
        """
            Override by Softhealer Technologies Pvt. Ltd.
        The function is used to handle barcode scanning in a purchase order,
        updating the quantity of a product or creating a new order line if the product is not already in
        the order.

        :param barcode: The barcode parameter is the barcode value that is scanned by the barcode
        scanner. It is used to search for the corresponding product in the order lines
        """
        company_sudo = self.env.company
        is_last_scanned = False
        sequence = 0
        warn_sound_code = ""
        if company_sudo.sh_purchase_barcode_scanner_last_scanned_color:
            is_last_scanned = True

        if company_sudo.sh_purchase_barcode_scanner_move_to_top:
            sequence = -1

        if company_sudo.sh_purchase_barcode_scanner_warn_sound:
            warn_sound_code = "SH_BARCODE_SCANNER_"

        if company_sudo.sh_purchase_barcode_scanner_auto_close_popup:
            warn_sound_code += "AUTO_CLOSE_AFTER_" + \
                str(self.env.company.sudo(
                ).sh_purchase_barcode_scanner_auto_close_popup) + "_MS&"

        # step 1 increase product qty by 1 if product not in order line than create new order line.
        if self and self.state and self.state not in ("cancel", "done"):
            self.order_line.update(
                {"sh_purchase_barcode_scanner_is_last_scanned": False, "sequence": 0})
            search_lines = False
            domain = []
            if company_sudo.sh_purchase_barcode_scanner_type == "barcode":
                search_lines = self.order_line.filtered(
                    lambda ol: ol.product_id.barcode == barcode)
                domain = [("barcode", "=", barcode)]

            elif company_sudo.sh_purchase_barcode_scanner_type == "int_ref":
                search_lines = self.order_line.filtered(
                    lambda ol: ol.product_id.default_code == barcode)
                domain = [("default_code", "=", barcode)]

            elif company_sudo.sh_purchase_barcode_scanner_type == "sh_qr_code":
                search_lines = self.order_line.filtered(
                    lambda ol: ol.product_id.sh_qr_code == barcode)
                domain = [("sh_qr_code", "=", barcode)]

            elif company_sudo.sh_purchase_barcode_scanner_type == "all":
                search_lines = self.order_line.filtered(lambda ol: barcode in (
                    ol.product_id.barcode, ol.product_id.default_code, ol.product_id.sh_qr_code))
                domain = ["|", "|", ("default_code", "=", barcode),
                          ("barcode", "=", barcode),
                          ("sh_qr_code", "=", barcode)]

            if search_lines:
                line = search_lines[:1]
                line.product_qty = line.product_qty + 1
                line.sh_purchase_barcode_scanner_is_last_scanned = is_last_scanned
                line.sequence = sequence

            else:
                new_domain = expression.AND(
                    [domain, [("purchase_ok", "=", True)]])
                search_product = self.env["product.product"].search(
                    new_domain, limit=1)
                if search_product:
                    order_line_val = {"name": search_product.name,
                                      "product_id": search_product.id,
                                      "product_qty": 1,
                                      "price_unit": search_product.lst_price,
                                      "date_planned": str(fields.Date.today()),
                                      "order_id": self.id,
                                      "sh_purchase_barcode_scanner_is_last_scanned": is_last_scanned,
                                      "sequence": sequence}
                    if search_product.uom_id:
                        order_line_val.update(
                            {"product_uom": search_product.uom_po_id.id})

                    new_order_line = self.order_line.new(order_line_val)
                    new_order_line.onchange_product_id()

                else:
                    raise UserError(
                        _(warn_sound_code + "Scanned Internal Reference/Barcode/QR Code '%s' does not exist in any product!") % (barcode))

        # step 2 make sure order in proper state.
        else:
            selections = self.fields_get()["state"]["selection"]
            value = next((v[1] for v in selections if v[0]
                         == self.state), self.state)
            raise UserError(
                _(warn_sound_code + "You can not scan item in %s state.") % (value))
