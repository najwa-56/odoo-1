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

_logger = logging.getLogger(__name__)

class pos_config(models.Model):
    _inherit = 'pos.config' 

    allow_multi_uom = fields.Boolean('Product multi uom', default=True)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_multi_uom = fields.Boolean(related='pos_config_id.allow_multi_uom', readonly=False)

class product_multi_uom(models.Model):
    _name = 'product.multi.uom'
    _order = "sequence desc"

    multi_uom_id = fields.Many2one('uom.uom','Unit of measure')
    product_id = fields.Many2one('product.product','Product')
    price = fields.Float("Sale Price",default=0)
    sequence = fields.Integer("Sequence",default=1)

    # @api.multi
    @api.onchange('multi_uom_id')
    def unit_id_change(self):
        domain = {'multi_uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        return {'domain': domain}

class product_product(models.Model):
    _inherit = 'product.product'
    
    has_multi_uom = fields.Boolean('Has multi UOM')
    multi_uom_ids = fields.One2many('product.multi.uom','product_id')


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _prepare_invoice_line(self, order_line):
        result = super()._prepare_invoice_line(order_line)
        result['product_uom_id'] = order_line.product_uom.id or order_line.product_uom_id.id
        return result
        
class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    product_uom = fields.Many2one('uom.uom','Unit of measure')

class StockPicking(models.Model):
    _inherit='stock.picking'

    def _prepare_stock_move_vals(self, first_line, order_lines):
        res = super(StockPicking, self)._prepare_stock_move_vals(first_line, order_lines)
        res['product_uom'] = first_line.product_uom.id or first_line.product_id.uom_id.id,
        return res

    def _create_move_from_pos_order_lines(self, lines):
        self.ensure_one()
        # lines_by_product = groupby(sorted(lines, key=lambda l: l.product_id.id), key=lambda l: l.product_id.id)
        lines_by_product = groupby(sorted(lines, key=lambda l: l.product_id.id), key=lambda l: (l.product_id.id,l.product_uom.id))

        move_vals = []
        for dummy, olines in lines_by_product:
            order_lines = self.env['pos.order.line'].concat(*olines)
            move_vals.append(self._prepare_stock_move_vals(order_lines[0], order_lines))
        moves = self.env['stock.move'].create(move_vals)
        confirmed_moves = moves._action_confirm()
        confirmed_moves._add_mls_related_to_order(lines, are_qties_done=True)

    # def _create_move_from_pos_order_lines(self, lines):
    #     self.ensure_one()
    #     lines_by_product = groupby(sorted(lines, key=lambda l: l.product_id.id), key=lambda l: (l.product_id.id,l.product_uom.id))
    #     for product, nlines in lines_by_product:
    #         order_lines = self.env['pos.order.line'].concat(*nlines)            
    #         first_line = order_lines[0]
    #         current_move = self.env['stock.move'].create(
    #             self._prepare_stock_move_vals(first_line, order_lines)
    #         )
    #         if first_line.product_id.tracking != 'none' and (self.picking_type_id.use_existing_lots or self.picking_type_id.use_create_lots):
    #             for line in order_lines:
    #                 sum_of_lots = 0
    #                 for lot in line.pack_lot_ids.filtered(lambda l: l.lot_name):
    #                     if line.product_id.tracking == 'serial':
    #                         qty = 1
    #                     else:
    #                         qty = abs(line.qty)
    #                     ml_vals = current_move._prepare_move_line_vals()
    #                     ml_vals.update({'qty_done':qty})
    #                     if self.picking_type_id.use_existing_lots:
    #                         existing_lot = self.env['stock.production.lot'].search([
    #                             ('company_id', '=', self.company_id.id),
    #                             ('product_id', '=', line.product_id.id),
    #                             ('name', '=', lot.lot_name)
    #                         ])
    #                         if not existing_lot and self.picking_type_id.use_create_lots:
    #                             existing_lot = self.env['stock.production.lot'].create({
    #                                 'company_id': self.company_id.id,
    #                                 'product_id': line.product_id.id,
    #                                 'name': lot.lot_name,
    #                             })
    #                         ml_vals.update({
    #                             'lot_id': existing_lot.id,
    #                         })
    #                     else:
    #                         ml_vals.update({
    #                             'lot_name': lot.lot_name,
    #                         })
    #                     self.env['stock.move.line'].create(ml_vals)
    #                     sum_of_lots += qty
    #                 if abs(line.qty) != sum_of_lots:
    #                     difference_qty = abs(line.qty) - sum_of_lots
    #                     ml_vals = current_move._prepare_move_line_vals()
    #                     if line.product_id.tracking == 'serial':
    #                         ml_vals.update({'qty_done': 1})
    #                         for i in range(int(difference_qty)):
    #                             self.env['stock.move.line'].create(ml_vals)
    #                     else:
    #                         ml_vals.update({'qty_done': difference_qty})
    #                         self.env['stock.move.line'].create(ml_vals)
    #         else:
    #             # current_move.quantity_done = abs(sum(order_lines.mapped('qty')))
    #             confirmed_moves = current_move._action_confirm()
    #             confirmed_moves._add_mls_related_to_order(lines, are_qties_done=True)
    #             confirmed_moves.picked = True
    #             self._link_owner_on_return_picking(lines)


class PosSession(models.Model):
    _inherit = 'pos.session'


    @api.model
    def _pos_ui_models_to_load(self):
        result = super()._pos_ui_models_to_load()
        if self.config_id.allow_multi_uom:
            new_model = 'product.multi.uom'
            if new_model not in result:
                result.append(new_model)
        return result

    def _loader_params_product_product(self):
        result = super()._loader_params_product_product()
        result['search_params']['fields'].extend(['has_multi_uom','multi_uom_ids'])
        return result

    def _loader_params_product_multi_uom(self):
        return {'search_params': {'domain': [], 'fields': ['multi_uom_id','price'], 'load': False}}

    def _get_pos_ui_product_multi_uom(self, params):
        result = self.env['product.multi.uom'].search_read(**params['search_params'])
        for res in result:
            uom_id = self.env['uom.uom'].browse(res['multi_uom_id'])
            res['multi_uom_id'] = [uom_id.id,uom_id.name] 
        return result