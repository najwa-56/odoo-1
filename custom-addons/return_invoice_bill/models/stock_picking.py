# -*- coding: utf-8 -*-
##############################################################################
#

#
##############################################################################
from odoo import api, fields, models


class StockPicking(models.Model):
    """This class extends the 'stock.picking' model to add a method for
    retrieving credit notes and debit notes related
    to the picking, and generating actions for viewing them."""
    _inherit = 'stock.picking'

    picking_type_name = fields.Char(string='Picking Type Name',
                                    help='Name of picking type')
    return_invoice_count = fields.Char(string="Counts",
                                       compute='_compute_return_invoice_count',
                                       help="counts of return invoices")
    is_paid = fields.Boolean(string='Is Paid',
                             help='Value will be True when order has paid '
                                  'otherwise False.')
    second_deilvery = fields.Boolean('second_deilvery')
   

    @api.model_create_multi
    def create(self, vals):
        if self._context.get('exchange',False):
            for val in vals:
                if val.get('origin',False):
                    sale_order_id = self.env['sale.order'].search([('name','=',val.get('origin'))])
                    if sale_order_id:
                        if  sale_order_id.order_line[0] and  sale_order_id.order_line[0].route_id:
                            rule_id = self.env['stock.rule'].search([('route_id', '=', sale_order_id.order_line[0].route_id.id)])
                            picking_type_id = rule_id.picking_type_id
                            location_id = rule_id.location_src_id
                            if picking_type_id and location_id :
                                val['picking_type_id'] = picking_type_id.id
                                val['location_id'] = location_id.id
                                val['second_deilvery'] = True
        res =  super().create(vals)
        return res

    def action_get_credit_note(self):
        """Generates an action to view reversal credit notes
         based on the context."""
        self.ensure_one()
        credit_notes = self.sale_id.invoice_ids.filtered(
            lambda x: x.move_type == 'out_refund')
        return {
            'type': 'ir.actions.act_window',
            'name': _(
                'Reversal of Credit Note: %s') % self.sale_id.invoice_ids.filtered(
                lambda x: x.move_type == 'out_invoice').name,
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', credit_notes.ids)],
        }

    def action_get_debit_note(self):
        """Generates an action to view reversal  debit notes
                based on the context."""
        debit_notes = self.purchase_id.invoice_ids.filtered(
            lambda x: x.move_type == 'in_refund')
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _(
                'Reversal of Debit Note: %s') % self.purchase_id.invoice_ids.filtered(
                lambda x: x.move_type == 'in_invoice').name,
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', debit_notes.ids)]
        }

    @api.depends('return_invoice_count')
    def _compute_return_invoice_count(self):
        self.return_invoice_count = self.return_count




class StockMove(models.Model):
    """This class extends the 'stock.picking' model to add a method for
    retrieving credit notes and debit notes related
    to the picking, and generating actions for viewing them."""
    _inherit = 'stock.move'


    @api.model_create_multi
    def create(self, vals):
        if self._context.get('exchange',False):
            for val in vals:
                if val.get('origin',False):
                    sale_order_id = self.env['sale.order'].search([('name','=',val.get('origin'))])
                    if sale_order_id:
                        if  sale_order_id.order_line[0] and  sale_order_id.order_line[0].route_id:
                            rule_id = self.env['stock.rule'].search([('route_id', '=', sale_order_id.order_line[0].route_id.id)])
                            picking_type_id = rule_id.picking_type_id
                            location_id = rule_id.location_src_id
                            if picking_type_id and location_id :
                                val['picking_type_id'] = picking_type_id.id
                                val['location_id'] = location_id.id
        res =  super().create(vals)

        return res