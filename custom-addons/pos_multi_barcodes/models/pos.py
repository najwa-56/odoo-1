# -*- coding: utf-8 -*-


import logging
from odoo import api, fields, models, tools, _
import odoo.addons.decimal_precision as dp
import json

from itertools import groupby
_logger = logging.getLogger(__name__)

class pos_multi_barcode_opt(models.Model):
    _name = 'pos.multi.barcode.options'

    name = fields.Char('Barcode',required=True)
    qty = fields.Float("Quantity")
    price = fields.Float("Price")
    unit = fields.Many2one("uom.uom",string="Unit")
    product_id = fields.Many2one("product.product",string="Product")
    cost = fields.Float("Cost")  # Added cost field



    @api.onchange('unit')
    def unit_id_change(self):
        domain = {'unit': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        return {'domain': domain}


class product_product(models.Model):
    _inherit = 'product.product'

    pos_multi_barcode_option = fields.One2many('pos.multi.barcode.options','product_id',string='Barcodes')
    barcode_options = fields.Text("New Barcode", compute="_compute_barcode_options")

    def _compute_barcode_options(self):
        for record in self:
            if record.pos_multi_barcode_option:
                multi_uom_list = []
                for multi_uom in record.pos_multi_barcode_option:
                    multi_uom_list.append(multi_uom.name)
                record.barcode_options = json.dumps(multi_uom_list)
            else:
                record.barcode_options = json.dumps([])

class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    product_uom = fields.Many2one('uom.uom','Unit of measure')
    cost_UOM = fields.Float("UOM Cost", compute="_compute_cost", store=True)  # Added cost field with compute method

    @api.depends('product_id')
    def _compute_cost(self):
        for line in self:
            barcode_option = self.env['pos.multi.barcode.options'].search([
                ('product_id', '=', line.product_id.id)
            ], limit=1)
            line.cost = barcode_option.cost if barcode_option else 0.0


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



class PosSession(models.Model):
    _inherit = 'pos.session'

    def _pos_data_process(self, loaded_data):
        super()._pos_data_process(loaded_data)
        loaded_data['multi_barcode_id'] = {multi_barcode['id']: multi_barcode for multi_barcode in loaded_data['pos.multi.barcode.options']}

    @api.model
    def _pos_ui_models_to_load(self):
        result = super()._pos_ui_models_to_load()
        new_model = 'pos.multi.barcode.options'
        if new_model not in result:
            result.append(new_model)
        return result

    def _loader_params_product_product(self):
        result = super()._loader_params_product_product()
        result['search_params']['fields'].extend(['pos_multi_barcode_option','barcode_options'])
        return result

    def _loader_params_pos_multi_barcode_options(self):
        return {'search_params': {'domain': [], 'fields': ['name','product_id','qty','price','unit'], 'load': False}}

    def _get_pos_ui_pos_multi_barcode_options(self, params):
        result = self.env['pos.multi.barcode.options'].search_read(**params['search_params'])
        for res in result:
            uom_id = self.env['uom.uom'].browse(res['unit'])
            res['unit'] = [uom_id.id,uom_id.name]
        return result