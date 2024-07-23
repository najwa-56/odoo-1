# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies Pvt. Ltd.


from odoo import fields, models


class ShMrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    sh_bom_barcode_scanner_is_last_scanned = fields.Boolean(
        string="Last Scanned?")
