# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models


class ShStockMoveLine(models.Model):
    _inherit = "stock.move.line"

    sequence = fields.Integer(default=0)
    sh_inventory_barcode_scanner_is_last_scanned = fields.Boolean(string="Last Scanned?")
