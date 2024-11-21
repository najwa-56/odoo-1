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

    # UOM field
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", domain="[('category_id', '=', category_id)]", index=True)

    # Adjusted Quantity field
    qty = fields.Float(string='Adjusted Quantity', compute='_compute_qty', store=True)

    # UOM Name field
    uom_name = fields.Char(string="UOM Name", related="uom_id.name", store=True)

    # Ratio field (related to the product.multi.uom.price)
    ratio = fields.Float(string="Ratio", related="uom_id.ratio", store=True)

    @api.depends('uom_id')
    def _compute_qty(self):
        """ Compute the adjusted quantity based on the ratio from product.multi.uom.price """
        for record in self:
            if record.uom_id:
                # Search for the corresponding multi_uom_price record
                multi_uom_price = self.env['product.multi.uom.price'].search([
                    ('product_id', '=', record.product_id.id),
                    ('uom_id', '=', record.uom_id.id)
                ], limit=1)

                # Calculate adjusted quantity (quantity / ratio)
                if multi_uom_price and multi_uom_price.ratio:
                    record.qty = record.quantity / multi_uom_price.ratio
                else:
                    record.qty = record.quantity  # Default to quantity if ratio is not found

    def _select(self):
        select_str = super(AccountInvoiceReport, self)._select()
        select_str += """
            , line.product_uom_id as uom_id
            , multi_uom_price.ratio as ratio
            , line.product_uom_id as uom_name  -- Use as standard field, no JSON operator
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
            , line.product_uom_id
            , multi_uom_price.ratio
        """
        return group_by_str
