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

    uom_name = fields.Char(
        string="UOM Name",
        compute="_compute_get_uom_name",
        store=True
    )

    @api.depends('product_id', 'product_uom_id')
    def _compute_get_uom_name(self):
        for rec in self:
            uom_name = None
            if rec.product_id and rec.product_uom_id:
                # Check if multi_uom_price_id exists and filter by uom_id
                uom_price = rec.product_id.multi_uom_price_id.filtered(
                    lambda m: m.uom_id.id == rec.product_uom_id.id
                )
                uom_name = uom_price[0].name_field if uom_price else None

            # Fallback to product_uom_id name if no match is found
            rec.uom_name = uom_name or rec.product_uom_id.name