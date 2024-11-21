# -*- coding: utf-8 -*-
from odoo import models, fields, api



class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    uom_name = fields.Char('Uom Name', compute="_compute_get_uom_name", store=True, index=True)

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

    uom_name = fields.Char(string="UOM Name", store=True)

    def _select(self):
        select_str = super(AccountInvoiceReport, self)._select()
        select_str += ", line.uom_name as uom_name"
        return select_str

    def _group_by(self):
        group_by_str = super(AccountInvoiceReport, self)._group_by()
        group_by_str += ", line.uom_name"
        return group_by_str


    qty = fields.Float(string='Adjusted Quantity', compute='_compute_qty', store=True)

    @api.depends('quantity', 'product_id')
    def _compute_qty(self):
        for record in self:
            # Get the ratio from the related product.multi.uom.price model
            multi_uom_price = self.env['product.multi.uom.price'].search([
                ('product_id', '=', record.product_id.id),
                ('uom_id', '=', record.product_uom_id.id)
            ], limit=1)
            ratio = multi_uom_price.ratio if multi_uom_price else 1.0

            # Compute the qty
            record.qty = record.quantity / ratio if ratio else record.quantity

    def _select(self):
        select_str = super(AccountInvoiceReport, self)._select()
        select_str += """
                    , COALESCE(line.quantity / NULLIF(multi_uom_price.ratio, 0), 0) as qty
                """
        return select_str

    def _from(self):
        from_str = super(AccountInvoiceReport, self)._from()
        from_str += """
                    LEFT JOIN product_multi_uom_price AS multi_uom_price
                    ON multi_uom_price.product_id = line.product_id
                    AND multi_uom_price.uom_id = line.product_uom_id
                """
        return from_str

    def _group_by(self):
        group_by_str = super(AccountInvoiceReport, self)._group_by()
        group_by_str += ", line.quantity, multi_uom_price.ratio"
        return group_by_str
