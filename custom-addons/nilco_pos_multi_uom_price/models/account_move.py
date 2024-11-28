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
    qty = fields.Float(string="Adjusted Quantity", store=True)

    def _select(self):
        """Extend the SQL SELECT statement to include qty and uom_name."""
        select_str = super(AccountInvoiceReport, self)._select()
        select_str += """
            , line.uom_name as uom_name
            , (line.quantity) * (CASE WHEN move.move_type IN ('out_refund', 'in_receipt') THEN -1 ELSE 1 END) AS qty
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
        """
        return group_by_str

'''
''' 
class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    uom_name = fields.Char(string="UOM Name", store=True)
    qty = fields.Float(string="Adjusted Quantity", store=True)
    location_id = fields.Many2one('route.line', string='المسار', store=True, help="Location of route")
    partner_id = fields.Many2one('res.partner', string="Customer", readonly=True)

    def _select(self):
        """Extend the SQL SELECT statement to include qty, uom_name, and location_id."""
        select_str = super(AccountInvoiceReport, self)._select()
        select_str += """
            , line.uom_name as uom_name
            , (line.quantity) * (CASE WHEN move.move_type IN ('out_refund', 'in_receipt') THEN -1 ELSE 1 END) AS qty
            , partner.location_id as location_id
            
        """
        return select_str

    def _from(self):
        """Extend the SQL FROM statement to join with product_multi_uom_price and add location."""
        from_str = super(AccountInvoiceReport, self)._from()

        # Assuming that 'res_partner' might have already been joined, we avoid duplicating it
        if 'res_partner' not in from_str:
            from_str += """
                LEFT JOIN res_partner AS partner
                ON partner.id = move.partner_id
            """

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
            , partner.location_id
            
        """
        return group_by_str
'''



class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    uom_name = fields.Char(string="UOM Name", store=True)
    qty = fields.Float(string="Adjusted Quantity", store=True)
    location_id = fields.Many2one('route.line', string='المسار', store=True, help="Location of route")
    partner_id = fields.Many2one('res.partner', string="Customer", readonly=True, store=True)  # Added store=True

    def _select(self):
        """Extend the SQL SELECT statement to include qty, uom_name, location_id, and partner_id."""
        select_str = super(AccountInvoiceReport, self)._select()
        select_str += """
            , line.uom_name AS uom_name
            , (line.quantity) * (CASE WHEN move.move_type IN ('out_refund', 'in_receipt') THEN -1 ELSE 1 END) AS qty
            , partner.location_id AS location_id
            , partner.id AS partner_id  -- Added partner_id
        """
        return select_str

    def _from(self):
        """Extend the SQL FROM statement to join with product_multi_uom_price and add location."""
        from_str = super(AccountInvoiceReport, self)._from()

        # Ensure that 'res_partner' is joined only once
        if 'JOIN res_partner partner' not in from_str:
            from_str += """
                LEFT JOIN res_partner partner ON partner.id = move.partner_id
            """

        # Ensure 'product_multi_uom_price' is joined only once
        if 'JOIN product_multi_uom_price multi_uom_price' not in from_str:
            from_str += """
                LEFT JOIN product_multi_uom_price multi_uom_price ON
                    multi_uom_price.product_id = line.product_id AND
                    multi_uom_price.uom_id = line.product_uom_id
            """
        return from_str

    def _group_by(self):
        """Extend the SQL GROUP BY statement to include new fields."""
        group_by_str = super(AccountInvoiceReport, self)._group_by()
        group_by_str += """
            , line.uom_name
            , partner.location_id
            , partner.id  -- Added partner.id to GROUP BY
        """
        return group_by_str


