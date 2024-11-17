# -*- coding: utf-8 -*-
from odoo import models, fields, api



class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    uom_name = fields.Char('Uom Name', compute="_compute_get_uom_name")

    @api.depends('product_uom_id')
    def _compute_get_uom_name(self):
        for rec in self:
            uom_id = rec.product_id.multi_uom_price_id.filtered(lambda m :m.uom_id.id == rec.product_uom_id.id)
            if uom_id:
                rec.uom_name = uom_id[0].name_field
            else:
                rec.uom_name = rec.product_uom_id.name


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    uom_name = fields.Char(string="UOM Name", readonly=True)

    def _select(self):
        # Extend the SELECT clause to include the UOM name
        select_str = super(AccountInvoiceReport, self)._select()
        select_str += ", uom.name as uom_name"
        return select_str

    def _from(self):
        # Extend the FROM clause to include the UOM table
        from_str = super(AccountInvoiceReport, self)._from()
        from_str += """
              LEFT JOIN uom_uom uom ON uom.id = line.product_uom_id
          """
        return from_str

    def _group_by(self):
        # Extend the GROUP BY clause to include the UOM name
        group_by_str = super(AccountInvoiceReport, self)._group_by()
        group_by_str += ", uom.name"
        return group_by_str