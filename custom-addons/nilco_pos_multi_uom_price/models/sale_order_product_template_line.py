# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrderTemplateLine(models.Model):
    _inherit = "sale.order.template.line"

    @api.depends('product_id')
    def _compute_product_uom_id(self):
        for option in self:
            uom_price_id = option.product_id.multi_uom_price_id
            if uom_price_id:
                option.product_uom_id = uom_price_id[0].uom_id.id
            else:
                option.product_uom_id = option.product_id.uom_id