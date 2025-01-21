# -*- coding: utf-8 -*-
##############################################################################
#

#
##############################################################################
from odoo import api, fields, models


class StockReturnPicking(models.TransientModel):
    """Inherited this class to display the view, to add the cancel reason."""
    _inherit = 'stock.return.picking'

    picking_type_name = fields.Char(string='Picking Type Name',
                                    help='Name of the picking type')

    @api.model
    def default_get(self, fields):
        """Override of default_get method to set default values for fields
         in the wizard."""
        result = super(StockReturnPicking, self).default_get(fields)
        active_model = self.env.context['active_model']
        active_id = self.env.context['active_id']
        if active_model == 'stock.picking' and active_id:
            stock_picking = self.env[active_model].browse(active_id)
            picking_type = stock_picking.picking_type_id
            result['picking_type_name'] = self.env['ir.model.data'].search([
                ('model', '=', 'stock.picking.type'),
                ('res_id', '=', picking_type.id)
            ]).complete_name
        return result

    def _update_stock_picking(self):
        """Update the 'is_paid' field of the active stock picking to indicate
        payment. This function is typically called when processing returns with
        credit or debit notes."""
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        if active_model == 'stock.picking' and active_id:
            stock_picking = self.env[active_model].browse(active_id)
            stock_picking.is_paid = True

    def _get_return_action(self):
        """
        Retrieve the action for returning a move, specifically for credit notes.
        Returns:
            ir.actions.actions: Action object for returning moves with credit
            notes.
        """
        return self.env["ir.actions.actions"]._for_xml_id("return_invoice_bill.return_move_action")

    def action_returns_with_credit_note(self):
        """
        Perform the action of returning moves with credit notes and update the
        stock picking accordingly.
        Returns:
            ir.actions.actions: Action object for returning moves with credit
            notes.
        """
        self._update_stock_picking()
        return self._get_return_action()

    def action_returns_with_debit_note(self):
        """
        Perform the action of returning moves with debit notes and update the
        stock picking accordingly.
        Returns:
            ir.actions.actions: Action object for returning moves with debit
            notes.
        """
        self._update_stock_picking()
        return self._get_return_action()


    def action_create_exchanges(self):
        """ Create a return for the active picking, then create a return of
        the return for the exchange picking and open it."""
        action = self.create_returns()
        if action.get('res_id'):
            new_picking = self.env['stock.picking'].browse(int(action.get('res_id')))
            new_picking.button_validate()

        proc_list = []
        for line in self.product_return_moves:
            if not line.move_id:
                continue
            proc_values = self._get_proc_values(line)
            proc_list.append(self.env["procurement.group"].with_context(exchange=True).Procurement(
                line.product_id, line.quantity, line.uom_id,
                line.move_id.location_dest_id or self.picking_id.location_dest_id,
                line.product_id.display_name, self.picking_id.origin, self.picking_id.company_id,
                proc_values,
            ))
        if proc_list:
            self.env['procurement.group'].with_context(exchange=True).run(proc_list)
        exchange_picking_id = self.env['stock.picking'].search([('state','=','assigned'),('group_id','=',new_picking.group_id.id)])
        exchange_picking_id.button_validate()
        return action

    def _get_proc_values(self, line):
        self.ensure_one()
        return {
            'group_id': self.picking_id.group_id,
            'date_planned': line.move_id.date or fields.Datetime.now(),
            'warehouse_id': self.picking_id.picking_type_id.warehouse_id,
            'partner_id': self.picking_id.partner_id.id,
            'location_dest_id': line.move_id.location_dest_id or self.picking_id.location_dest_id,
            'location_id': line.move_id.location_id or self.picking_id.location_id,
            'company_id': self.picking_id.company_id,
        }




    # def _prepare_move_default_values(self, return_line, new_picking):
    #     vals = super(StockReturnPicking, self)._prepare_move_default_values(return_line, new_picking)
    #     print("self._prepare_move_default_values context ===================",self._context)
    #     is_exchange = self._context.get('is_exchange',False)
    #     if return_line.to_refund and not is_exchange:
    #         vals['to_refund'] = True
    #     return vals

