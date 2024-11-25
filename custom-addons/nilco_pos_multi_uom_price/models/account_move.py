# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api
_logger = logging.getLogger(__name__)


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





''' 
class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    uom_name = fields.Char(string="UOM Name", store=True)
    qty = fields.Float(string="Adjusted Quantity", compute="_compute_qty", store=True)

    @api.depends('quantity', 'product_id', 'product_uom_id')
    def _compute_qty(self):
        """Compute Adjusted Quantity as quantity / ratio."""
        for record in self:
            if record.product_id and record.product_uom_id:
                # Fetch the ratio from the related product.multi.uom.price record
                multi_uom_price = self.env['product.multi.uom.price'].search([
                    ('product_id', '=', record.product_id.id),
                    ('uom_id', '=', record.product_uom_id.id)
                ], limit=1)
                ratio = multi_uom_price.ratio if multi_uom_price else 1.0  # Default ratio is 1.0
                _logger.info(f"Record {record.id}: quantity={record.quantity}, ratio={ratio}")
                record.qty = record.quantity / ratio if ratio > 0 else 0.0
            else:
                _logger.warning(f"Record {record.id}: Missing product or UOM")
                record.qty = 0.0  # Default to zero if fields are missing

    def _select(self):
        """Extend the SQL SELECT statement to include qty and uom_name."""
        select_str = super(AccountInvoiceReport, self)._select()
        select_str += """
            , line.uom_name as uom_name
            , COALESCE(line.quantity / NULLIF(COALESCE(multi_uom_price.ratio, 1.0), 0), 0) as qty
        """
        return select_str

    def _from(self):
        """Extend the SQL FROM statement to join with product_multi_uom_price."""
        from_str = super(AccountInvoiceReport, self)._from()
        from_str += """
            LEFT JOIN product_multi_uom_price AS multi_uom_price
            ON multi_uom_price.product_id = line.product_id
            AND multi_uom_price.uom_id = line.product_uom_id
        """
        return from_str

    def _group_by(self):
        """Extend the SQL GROUP BY statement to include new fields."""
        group_by_str = super(AccountInvoiceReport, self)._group_by()
        group_by_str += """
            , line.uom_name
            , line.quantity
            , multi_uom_price.ratio
        """
        return group_by_str


'''


'''class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    uom_name = fields.Char(string="UOM Name", store=True)
    qty = fields.Float(string="Adjusted Quantity", compute="_compute_qty", store=True)

    @api.depends('quantity', 'product_id', 'product_uom_id')
    def _compute_qty(self):
        """Compute Adjusted Quantity as quantity / ratio."""
        for record in self:
            if record.product_id and record.product_uom_id:
                # Fetch the ratio from the related product.multi.uom.price record
                multi_uom_price = self.env['product.multi.uom.price'].search([
                    ('product_id', '=', record.product_id.id),
                    ('uom_id', '=', record.product_uom_id.id)
                ], limit=1)
                ratio = multi_uom_price.ratio if multi_uom_price else 1.0  # Default ratio is 1.0
                _logger.info(f"Record {record.id}: Product={record.product_id.id}, "
                             f"UOM={record.product_uom_id.id}, Quantity={record.quantity}, Ratio={ratio}")
                record.qty = round(record.quantity / ratio, 2) if ratio > 0 else 0.0
            else:
                _logger.warning(f"Record {record.id}: Missing product or UOM")
                record.qty = 0.0  # Default to zero if fields are missing

    def _select(self):
        """Extend the SQL SELECT statement to include qty and uom_name."""
        select_str = super(AccountInvoiceReport, self)._select()
        select_str += """
            , line.uom_name as uom_name
            , line.quantity as qty  -- Just select the original quantity without division
        """
        return select_str

    def _from(self):
        """Extend the SQL FROM statement to join with product_multi_uom_price."""
        from_str = super(AccountInvoiceReport, self)._from()
        from_str += """
            LEFT JOIN product_multi_uom_price AS multi_uom_price
            ON multi_uom_price.product_id = line.product_id
            AND multi_uom_price.uom_id = line.product_uom_id
        """
        return from_str

    def _group_by(self):
        """Extend the SQL GROUP BY statement to include new fields."""
        group_by_str = super(AccountInvoiceReport, self)._group_by()
        group_by_str += """
            , line.uom_name
            , line.quantity
            , multi_uom_price.ratio
        """
        return group_by_str
'''

''' 
class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    uom_name = fields.Char(string="UOM Name", store=True)
    qty = fields.Float(string="Adjusted Quantity", compute="_compute_qty", store=True)

    @api.depends('quantity', 'product_id', 'product_uom_id', 'move_type')
    def _compute_qty(self):
        """Compute Adjusted Quantity as quantity / ratio, adjusted for refunds."""
        for record in self:
            if record.product_id and record.product_uom_id:
                # Fetch the ratio from the related product.multi.uom.price record
                multi_uom_price = self.env['product.multi.uom.price'].search([
                    ('product_id', '=', record.product_id.id),
                    ('uom_id', '=', record.product_uom_id.id)
                ], limit=1)
                ratio = multi_uom_price.ratio if multi_uom_price else 1.0  # Default ratio is 1.0

                # Adjust quantity based on the move type
                adjusted_quantity = record.quantity * (-1 if record.move_type in ('out_refund', 'in_receipt') else 1)

                # Compute adjusted quantity divided by ratio
                record.qty = round(adjusted_quantity / ratio, 2) if ratio > 0 else 0.0
            else:
                record.qty = 0.0  # Default to zero if fields are missing

    def _select(self):
        """Extend the SQL SELECT statement to include qty and uom_name."""
        select_str = super(AccountInvoiceReport, self)._select()
        select_str += """
            , line.uom_name as uom_name
            , (line.quantity * (CASE WHEN move.move_type IN ('out_refund', 'in_receipt') THEN -1 ELSE 1 END)) / 
              COALESCE(multi_uom_price.ratio, 1.0) AS qty
        """
        return select_str

    def _from(self):
        """Extend the SQL FROM statement to join with product_multi_uom_price."""
        from_str = super(AccountInvoiceReport, self)._from()
        from_str += """
            LEFT JOIN product_multi_uom_price AS multi_uom_price
            ON multi_uom_price.product_id = line.product_id
            AND multi_uom_price.uom_id = line.product_uom_id
        """
        return from_str

    def _group_by(self):
        """Extend the SQL GROUP BY statement to include new fields."""
        group_by_str = super(AccountInvoiceReport, self)._group_by()
        group_by_str += """
            , line.uom_name
            , line.quantity
            , multi_uom_price.ratio
        """
        return group_by_str

'''
from odoo import models, fields, api

class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    uom_name = fields.Char(string="UOM Name", store=True)
    qty = fields.Float(string="Adjusted Quantity", compute="_compute_qty", store=True)

    @api.depends('quantity', 'product_id', 'product_uom_id', 'move_type')
    def _compute_qty(self):
        """Compute Adjusted Quantity as quantity / ratio, adjusted for refunds."""
        for record in self:
            if record.product_id and record.product_uom_id:
                # Fetch the ratio from the product.multi.uom.price model
                multi_uom_price = self.env['product.multi.uom.price'].search([
                    ('product_id', '=', record.product_id.id),
                    ('uom_id', '=', record.product_uom_id.id)
                ], limit=1)
                ratio = multi_uom_price.ratio if multi_uom_price else 1.0  # Default ratio is 1.0

                # Adjust for refunds or receipt moves
                base_quantity = record.quantity * (-1 if record.move_type in ('out_refund', 'in_receipt') else 1)

                # Avoid multiple divisions or dividing by zero
                if ratio > 0:
                    record.qty = round(base_quantity / ratio, 2)
                else:
                    record.qty = 0.0
            else:
                record.qty = 0.0

    def _select(self):
        """Extend the SQL SELECT statement to include qty and uom_name."""
        select_str = super(AccountInvoiceReport, self)._select()
        select_str += """
            , line.uom_name as uom_name
            , (line.quantity * (CASE WHEN move.move_type IN ('out_refund', 'in_receipt') THEN -1 ELSE 1 END)) / 
              NULLIF(COALESCE(multi_uom_price.ratio, 1.0), 0) AS qty
        """
        return select_str

    def _from(self):
        """Extend the SQL FROM statement to join with product_multi_uom_price."""
        from_str = super(AccountInvoiceReport, self)._from()
        from_str += """
            LEFT JOIN product_multi_uom_price AS multi_uom_price
            ON multi_uom_price.product_id = line.product_id
            AND multi_uom_price.uom_id = line.product_uom_id
        """
        return from_str

    def _group_by(self):
        """Extend the SQL GROUP BY statement to include new fields."""
        group_by_str = super(AccountInvoiceReport, self)._group_by()
        group_by_str += """
            , line.uom_name
            , multi_uom_price.ratio
        """
        return group_by_str
