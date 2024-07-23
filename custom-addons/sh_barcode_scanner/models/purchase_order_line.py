# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies Pvt. Ltd.

from odoo import fields, models


class ShPurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    sh_purchase_barcode_scanner_is_last_scanned = fields.Boolean(
        string="Last Scanned?")
