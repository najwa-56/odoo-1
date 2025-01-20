# -*- coding: utf-8 -*-

from psycopg2 import sql

from odoo import tools
from odoo import api, fields, models


class ReportMergeObject(models.Model):
    _name = 'report.merge.object'
    _auto = False
    _description = "Report Merge Object"

    product_id = fields.Many2one('product.product')
    categ_id = fields.Many2one(related="product_id.categ_id",store=True)
    unit_id = fields.Many2one(related='product_id.uom_id',store=True)
    available_qty1 = fields.Float(related="product_id.qty_available",string='Available Qty')
    available_qty = fields.Float(compute="calculated_qty",string='Available Qty',store=True)

    @api.depends('product_id')
    def calculated_qty(self):
        for rec in self:
            if rec.product_id and rec.available_qty1:
                rec.available_qty = rec.product_id.qty_available

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'report_merge_object')
        params = []

        query = """
                create or replace view report_merge_object as (
                select row_number() OVER() AS ID,
                sub.product_id AS product_id
                from(

                SELECT R.id AS id,R.id AS product_id FROM product_product AS R

                ) AS Sub )
               """
        self.env.cr.execute(query)

