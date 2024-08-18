# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    discount_price = fields.Float(string="Discount Price", default=0.0)

    @api.onchange('discount_price')
    def _onchange_discount_price(self):
        """
            Approach to computing the percentage of discount based on the discounted price
        """
        for rec in self:
            if rec.discount_price <= (rec.quantity * rec.price_unit):
                if rec.discount_price == 0.00:
                    rec.update({
                        'discount': 0.00
                    })
                else:
                    rec.update({
                        'discount': (rec.discount_price * 100)/(rec.quantity * rec.price_unit)
                    })
            elif(rec.discount_price > rec.price_subtotal):
                raise ValidationError(_(
                "Discounted amount for product '%(product)s' must be less than '%(amount)s'.",
                product=rec.product_id.name,
                amount=rec.quantity * rec.price_unit
            ))

    @api.onchange('discount')
    def _onchange_discount(self):
        for rec in self:
            rec.update({
                'discount_price': (rec.quantity * rec.price_unit * rec.discount) / 100
            })