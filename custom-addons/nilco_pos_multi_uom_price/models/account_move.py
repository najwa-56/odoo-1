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

    # UOM Field
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", domain="[('category_id', '=', category_id)]", index=True)

    # Ratio field computed from the UOM
    ratio = fields.Float(string="Ratio", compute="_compute_ratio", store=True)

    # UOM Name field
    uom_name = fields.Char(string="UOM Name", related="uom_id.name", store=True)

    # Adjusted Quantity field
    qty = fields.Float(string='Adjusted Quantity', compute='_compute_qty', store=True)

    @api.depends('uom_id')
    def _compute_ratio(self):
        """ Compute the ratio based on the UOM """
        for record in self:
            record.ratio = record.uom_id.ratio if record.uom_id else 1.0

    @api.depends('quantity', 'ratio')
    def _compute_qty(self):
        """ Compute the adjusted quantity based on the ratio """
        for record in self:
            if record.ratio > 0:
                record.qty = record.quantity / record.ratio
            else:
                record.qty = record.quantity  # Avoid division by zero or invalid ratio

    def _select(self):
        select_str = super(AccountInvoiceReport, self)._select()
        select_str += """
            , line.uom_name as uom_name
            , COALESCE(line.quantity / NULLIF(line.ratio, 0), 0) as qty
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
        group_by_str += """
            , line.uom_name
            , line.quantity
            , line.ratio
        """
        return group_by_str
