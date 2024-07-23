# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies Pvt. Ltd.

from odoo import fields, models


class ShSaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    sh_sale_barcode_scanner_is_last_scanned = fields.Boolean(
        string="Last Scanned?")
