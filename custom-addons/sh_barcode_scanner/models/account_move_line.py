# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies Pvt. Ltd.

from odoo import api, fields, models


class ShAccountMoveLine(models.Model):
    _inherit = "account.move.line"

    sh_invoice_barcode_scanner_is_last_scanned = fields.Boolean(
        string="Last Scanned?")

    @api.depends('display_type')
    def _compute_sequence(self):
        """
            Overrides by Softhealer Technologies Pvt. Ltd.
        """
        seq_map = {
            'tax': 10000,
            'rounding': 11000,
            'payment_term': 12000,
        }
        for line in self:
            sequence = -1 if line.company_id.sh_invoice_barcode_scanner_move_to_top else seq_map.get(line.display_type, 100)
            line.sequence = sequence