# -*- coding: UTF-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models


class PurchaseReport(models.Model):
    _inherit = 'purchase.report'

    sh_sec_qty = fields.Float('Secondary Qty', readonly=True)
    sh_sec_uom = fields.Many2one("uom.uom", "Secondary UOM", readonly=True)

    # def _select(self):
    #     # return super(PurchaseReport, self)._select() + ", l.sh_sec_uom as sh_sec_uom" + ", sum(l.sh_sec_qty/line_uom.factor*product_uom.factor) as sh_sec_qty"
    #     return super(PurchaseReport, self)._select()

    def _group_by(self):
        return super(PurchaseReport, self)._group_by() + ", l.sh_sec_uom"
