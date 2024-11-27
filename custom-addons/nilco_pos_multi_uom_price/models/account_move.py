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


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    uom_name = fields.Char(string="UOM Name", store=True)
    qty = fields.Float(string="Adjusted Quantity", store=True)

    location_id = fields.Many2one(
        'route.line',
        string='المسار',
        help="Location of route.",
        related='partner_id.location_id',
        store=True
    )

    @api.model
    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        # Get the parent fields from the base model
        fields = fields.copy()  # Ensure we're not modifying the original fields dictionary
        fields['location_id'] = ", partner.location_id AS location_id"
        groupby += ', partner.location_id'
        return super(AccountInvoiceReport, self)._query(with_clause, fields, groupby, from_clause)
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

