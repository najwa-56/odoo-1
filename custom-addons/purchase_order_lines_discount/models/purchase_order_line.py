# Copyright (c) 2023 Sayed Hassan (sh-odoo@hotmail.com)

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    fixed_discount = fields.Float(string="Fixed Disc.", digits="Product Price", default=0.000)

    discount = fields.Float(string='% Disc.', digits='Discount', default=0.000)

    @api.onchange("discount_amount")
    def _onchange_discount(self):
        for line in self:
            if line.discount_method == 'per' and line.discount_amount != 0:
                self.fixed_discount = 0.0
                discount = line.discount_amount
                line.update({"discount": discount})
            if line.discount_amount == 0:
                discount = 0.000
                line.update({"discount": discount})

    @api.onchange("discount_amount")
    def _onchange_fixed_discount(self):
        for line in self:
            if line.discount_method == 'fix' and line.discount_amount != 0:
                self.discount = 0.0
                fixed_discount = line.discount_amount
                line.update({"fixed_discount": fixed_discount})
            if line.discount_amount == 0:
                fixed_discount = 0.0
                line.update({"fixed_discount": fixed_discount})

    def _prepare_account_move_line(self, move):
        """Prepare account.move.line values."""
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        for line in self:
            # Add fixed_discount to account.move.line values
            res.update({"fixed_discount": line.fixed_discount})
        return res

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    fixed_discount = fields.Float(string="Fixed Discount", digits="Product Price", default=0.000)
