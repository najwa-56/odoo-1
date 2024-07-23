# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import _, models
from odoo.osv import expression


class ShStockScrap(models.Model):
    _name = "stock.scrap"
    _inherit = ['barcodes.barcode_events_mixin', 'stock.scrap']

    def on_barcode_scanned(self, barcode):
        """
            Override by Softhealer Technologies Pvt. Ltd.
        The function is used to handle barcode scanning in a scrap wizard form,
        checking the scanned barcode against the product's barcode, internal reference, or QR code, and
        updating the scrap quantity accordingly.

        :param barcode: The `barcode` parameter is the barcode value that is scanned by the barcode
        scanner. It is used to identify the product in the system
        :return: The code is returning a dictionary with a "warning" key. The value of the "warning" key
        is another dictionary with "title" and "message" keys. The "title" key contains the string
        "Error!", and the "message" key contains a formatted error message.
        """
        warn_sound_code = ""
        company_sudo = self.env.company.sudo()

        if company_sudo.sh_scrap_barcode_scanner_warn_sound:
            warn_sound_code = "SH_BARCODE_SCANNER_"

        if company_sudo.sh_scrap_barcode_scanner_auto_close_popup:
            warn_sound_code += "AUTO_CLOSE_AFTER_" + \
                str(company_sudo.sh_scrap_barcode_scanner_auto_close_popup) + "_MS&"

        if self and self.state == "draft":
            domain = []
            product = False
            if company_sudo.sh_scrap_barcode_scanner_type == 'barcode':
                if self.product_id.barcode == barcode:
                    product = self.product_id
                domain = [("barcode", "=", barcode)]

            elif company_sudo.sh_scrap_barcode_scanner_type == 'int_ref':
                if self.product_id.default_code == barcode:
                    product = self.product_id
                domain = [("default_code", "=", barcode)]

            elif company_sudo.sh_scrap_barcode_scanner_type == 'sh_qr_code':
                if self.product_id.sh_qr_code == barcode:
                    product = self.product_id
                domain = [("sh_qr_code", "=", barcode)]

            elif company_sudo.sh_scrap_barcode_scanner_type == 'all':
                if barcode in (self.product_id.barcode, self.product_id.default_code, self.product_id.sh_qr_code):
                    product = self.product_id
                domain = ["|", "|", ("default_code", "=", barcode),
                          ("barcode", "=", barcode), ("sh_qr_code", "=", barcode)]

            if self.product_id:
                if product:
                    self.scrap_qty += 1
                else:
                    return {"warning": {
                        "title": _("Error!"),
                        "message": (warn_sound_code + "You can not change product after scan started. If you want to scan new product than pls create new scrap.")
                    }}
            else:
                # ---------------------------------------------------
                # We set below domain if scrap wizard form view opened from
                # delivery order scrap button rather than menu item.
                # because you only scraped products that are existed in delivery/picking lines.
                # ---------------------------------------------------
                if self._context.get('product_ids', False):
                    domain = expression.AND(
                        [domain, [("id", "in", self._context.get('product_ids'))]])

                search_product = self.env["product.product"].search(
                    domain, limit=1)
                if search_product:
                    self.product_id = search_product.id
                else:
                    return {"warning": {
                        "title": _("Error!"),
                        "message": (warn_sound_code + "Scanned Internal Reference/Barcode/QR Code '%s' does not exist in any product!" % (barcode))
                    }}

        else:
            if self.state:
                selections = self.fields_get()['state']['selection']
                value = next((v[1] for v in selections if v[0]
                             == self.state), self.state)
                return {'warning': {'title': _('Error!'), 'message': (warn_sound_code + 'You can not scan item in %s state.') % (value)}}
