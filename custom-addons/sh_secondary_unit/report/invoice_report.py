# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    sh_sec_uom = fields.Many2one(
        comodel_name="uom.uom", string="Secondary UOM")
    sh_sec_qty = fields.Float('Secondary Qty', readonly=True)

    def _select(self):
        return super()._select() + ", line.sh_sec_qty as sh_sec_qty, line.sh_sec_uom as sh_sec_uom"
