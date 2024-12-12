# -*- coding: utf-8 -*-

from odoo import models, api, fields 

class CrmTeam(models.Model):
    _inherit = "crm.team"

    route_id = fields.Many2one('stock.route', string='Route', domain=[('sale_selectable', '=', True)],
    default=False,
    )

class StockLocationRoute(models.Model):
    _inherit = "stock.route"

    salesteam_selectable = fields.Boolean('Sales Team', default=False)

class SaleOrderLine(models.Model):
    _inherit = ['sale.order.line']

    @api.model
    def create(self, vals):
        order_id = vals['order_id']
        order = self.env['sale.order'].browse(order_id)
        if order and order.team_id:
            if order.team_id.route_id:
                vals['route_id'] = order.team_id.route_id.id
        return super(SaleOrderLine, self).create(vals)
