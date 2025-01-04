# -*- coding: utf-8 -*-

import logging
from datetime import timedelta
from functools import partial
import psycopg2
from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError
from odoo.http import request
import odoo.addons.decimal_precision as dp
from itertools import groupby
import json

class StockPicking(models.Model):
    _inherit='stock.picking'

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        self._onchange_sale_order_template_id()
        return res

    sale_order_template_id = fields.Many2one(
        comodel_name='sale.order.template',
        string="Quotation Template",
        compute='_compute_sale_order_template_id',
        store=True, readonly=False, check_company=True, precompute=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    

    def _compute_sale_order_template_id(self):
        for order in self:
            company_template = order.company_id.sale_order_template_id
            if company_template and order.sale_order_template_id != company_template:
                if 'website_id' in self._fields and order.website_id:
                    # don't apply quotation template for order created via eCommerce
                    continue
                order.sale_order_template_id = order.company_id.sale_order_template_id.id


    @api.onchange('sale_order_template_id','location_id','location_dest_id')
    def _onchange_sale_order_template_id(self):
        if not self.sale_order_template_id:
            return

        sale_order_template = self.sale_order_template_id.with_context(lang=self.partner_id.lang)

        order_lines_data = [fields.Command.clear()]
        order_lines_data += [
            fields.Command.create(line.with_context(location_id=self.location_id , location_dest_id=self.location_dest_id,is_picking=True)._prepare_order_line_values())
            for line in sale_order_template.sale_order_template_line_ids
        ]

        # set first line to sequence -99, so a resequence on first page doesn't cause following page
        # lines (that all have sequence 10 by default) to get mixed in the first page
        if len(order_lines_data) >= 2:
            order_lines_data[1][2]['sequence'] = -99

        self.move_ids_without_package = order_lines_data

     

class SaleOrderTemplateLine(models.Model):
    _inherit = 'sale.order.template.line'

    def _prepare_order_line_values(self):
        res = super()._prepare_order_line_values()
        is_picking = self._context.get('is_picking',False)
        location_id = self._context.get('location_id',False)
        location_dest_id = self._context.get('location_dest_id',False)
        if is_picking:
            res.pop('display_type', None)  # Safely remove 'display_type' if it exists
            res['location_id'] = location_id and location_id.id or False
            res['location_dest_id'] = location_dest_id and location_dest_id.id or False


        return res