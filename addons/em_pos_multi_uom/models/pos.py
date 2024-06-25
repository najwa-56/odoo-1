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


_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = 'pos.config' 

    allow_multi_uom = fields.Boolean('Product multi uom', default=True)



class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_multi_uom = fields.Boolean(related='pos_config_id.allow_multi_uom', readonly=False)


class ProductMultiUom(models.Model):
    _name = 'product.multi.uom'
    _order = "sequence desc"

    multi_uom_id = fields.Many2one('uom.uom','Unit of measure')
    price = fields.Float("Sale Price",default=0)
    sequence = fields.Integer("Sequence",default=1)
    barcode = fields.Char("Barcode")
    product_tmp_id = fields.Many2one("product.template",string="Product")
    # product_id = fields.Many2one("product.product", compute="_compute_product_tmp_id", string="Product")

    # @api.depends('product_tmp_id')
    # def _compute_product_tmp_id(self):
    #     for record in self:
    #         if record.product_tmp_id.product_variant_ids:
    #             record.product_id = record.product_tmp_id.product_variant_ids.ids[0]
    #         else:
    #             record.product_id = 0

    # @api.multi
    @api.onchange('multi_uom_id')
    def unit_id_change(self):
        domain = {'multi_uom_id': [('category_id', '=', self.product_tmp_id.uom_id.category_id.id)]}        
        return {'domain': domain}

    # @api.model
    # def create(self, vals):
    #     if 'barcode' in vals and  vals['barcode'] != "":
    #         if vals['barcode']:
    #             barcodes = self.env['product.product'].sudo().search([('barcode','=',vals['barcode'])])
    #             barcodes2 = self.search([('barcode','=',vals['barcode'])])
    #             if barcodes or barcodes2:
    #                 raise UserError(_('A barcode can only be assigned to one product !'))
    #     return super(ProductMultiUom, self).create(vals)

    # # @api.multi
    # def write(self, vals):
    #     if 'barcode' in vals and vals['barcode'] != "":
    #         if vals['barcode']:
    #             barcodes = self.env['product.product'].sudo().search([('barcode','=',vals['barcode'])])
    #             barcodes2 = self.search([('barcode','=',vals['barcode'])])
    #             if barcodes or barcodes2:
    #                 raise UserError(_('A barcode can only be assigned to one product !'))
    #     return super(ProductMultiUom, self).write(vals)


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    has_multi_uom = fields.Boolean('Has multi UOM')
    multi_uom_ids = fields.One2many('product.multi.uom','product_tmp_id')
    new_barcode = fields.Text("New Barcode", compute="_compute_new_barcode")

    def _compute_new_barcode(self):
        for record in self:
            if record.multi_uom_ids:
                multi_uom_list = []
                for multi_uom in record.multi_uom_ids:
                    multi_uom_list.append(multi_uom.barcode)
                record.new_barcode = json.dumps(multi_uom_list)
            else:
                record.new_barcode = json.dumps([])

    # @api.model
    # def create(self, vals):
    #     if 'barcode' in vals and vals['barcode'] != "":
    #         if vals['barcode']:
    #             barcodes = self.env['product.multi.uom'].search([('barcode','=',vals['barcode'])])
    #             if barcodes:
    #                 raise UserError(_('A barcode can only be assigned to one product !'))
    #     return super(ProductTemplate, self).create(vals)

    # # @api.multi
    # def write(self, vals):
    #     if 'barcode' in vals and vals['barcode'] != "":
    #         if vals['barcode']:
    #             barcodes = self.env['product.multi.uom'].search([('barcode','=',vals['barcode'])])
    #             if barcodes:
    #                 raise UserError(_('A barcode can only be assigned to one product !'))
    #     return super(ProductTemplate, self).write(vals)

class PosOrder(models.Model):
    _inherit = "pos.order"

    def _prepare_invoice_line(self, order_line):
        result = super()._prepare_invoice_line(order_line)
        result['product_uom_id'] = order_line.product_uom.id or order_line.product_uom_id.id
        return result

class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    product_uom = fields.Many2one('uom.uom','Unit of measure')

    def _export_for_ui(self, orderline):
        res = super(PosOrderLine, self)._export_for_ui(orderline)
        if orderline.product_uom:
            res['product_uom'] = orderline.product_uom.id;
        else:
            res['product_uom'] = orderline.product_uom_id.id;
        return res


    def _launch_stock_rule_from_pos_order_lines(self):

        procurements = []
        for line in self:
            line = line.with_company(line.company_id)
            if not line.product_id.type in ('consu','product'):
                continue

            group_id = line._get_procurement_group()
            if not group_id:
                group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
                line.order_id.procurement_group_id = group_id

            values = line._prepare_procurement_values(group_id=group_id)
            product_qty = line.qty

            # procurement_uom = line.product_id.uom_id
            procurement_uom = line.product_uom or line.product_uom_id
            procurements.append(self.env['procurement.group'].Procurement(
                line.product_id, product_qty, procurement_uom,
                line.order_id.partner_id.property_stock_customer,
                line.name, line.order_id.name, line.order_id.company_id, values))
        if procurements:
            self.env['procurement.group'].run(procurements)

        # This next block is currently needed only because the scheduler trigger is done by picking confirmation rather than stock.move confirmation
        orders = self.mapped('order_id')
        for order in orders:
            pickings_to_confirm = order.picking_ids
            if pickings_to_confirm:
                # Trigger the Scheduler for Pickings
                pickings_to_confirm.action_confirm()
                tracked_lines = order.lines.filtered(lambda l: l.product_id.tracking != 'none')

                lines_by_tracked_product = groupby(sorted(tracked_lines, key=lambda l: l.product_id.id), key=lambda l: (l.product_id.id,l.product_uom.id))
                
                for product_id, lines in lines_by_tracked_product:
                    lines = self.env['pos.order.line'].concat(*lines)
                    moves = pickings_to_confirm.move_ids.filtered(lambda m: m.product_id.id == product_id)
                    moves.move_line_ids.unlink()
                    moves._add_mls_related_to_order(lines, are_qties_done=False)
                    moves._recompute_state()
        return True

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
    #     for product, lines in lines_by_product:
    #         order_lines = self.env['pos.order.line'].concat(*lines)            
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
    #             current_move.quantity_done = abs(sum(order_lines.mapped('qty')))

class PosSession(models.Model):
    _inherit = 'pos.session'

    def _pos_data_process(self, loaded_data):
        super()._pos_data_process(loaded_data)
        if self.config_id.allow_multi_uom:
            loaded_data['multi_uom_id'] = {multi_uom['id']: multi_uom for multi_uom in loaded_data['product.multi.uom']}

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
        result['search_params']['fields'].extend(['has_multi_uom','multi_uom_ids','new_barcode'])
        return result

    def _loader_params_product_multi_uom(self):
        return {'search_params': {'domain': [], 'fields': ['multi_uom_id','price','barcode'], 'load': False}}

    def _get_pos_ui_product_multi_uom(self, params):
        result = self.env['product.multi.uom'].search_read(**params['search_params'])
        for res in result:
            uom_id = self.env['uom.uom'].browse(res['multi_uom_id'])
            res['multi_uom_id'] = [uom_id.id,uom_id.name] 
        return result