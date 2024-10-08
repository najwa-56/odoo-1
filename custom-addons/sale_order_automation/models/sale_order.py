from odoo import api, fields, models, exceptions


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        res = super(SaleOrder, self.with_context(default_immediate_transfer=True)).action_confirm()
        for order in self:
            warehouse = order.warehouse_id
            if warehouse.is_delivery_set_to_done and order.picking_ids: 
                for picking in self.picking_ids:
                    if picking.state == 'cancel':
                        continue
                    for move in picking.move_ids:
                        move.quantity = move.product_qty
                    picking._autoconfirm_picking()
                    picking.button_validate()
                    for move_line in picking.move_ids_without_package:
                        move_line.quantity = move_line.product_uom_qty
                    
                    for mv_line in picking.move_ids.mapped('move_line_ids'):
                        # if not mv_line.button_validate and mv_line.reserved_qty or mv_line.reserved_uom_qty:
                        mv_line.quantity = mv_line.quantity_product_uom#.reserved_qty or mv_line.reserved_uom_qty

                    picking._action_done()

            if warehouse.create_invoice and not order.invoice_ids:
                order._create_invoices()
            if warehouse.validate_invoice and order.invoice_ids:
                for invoice in order.invoice_ids:
                    invoice.action_post()

        return res  
