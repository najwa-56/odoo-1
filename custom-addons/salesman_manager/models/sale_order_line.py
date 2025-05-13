from odoo import models, fields, api
from odoo.exceptions import AccessError
import logging
_logger = logging.getLogger(__name__)
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    #-----------------------------------------------------
    #calculating consumption
    # -----------------------------------------------------

    inventory_counting = fields.Float('الجرد', store=True)
    consumption = fields.Float('الصرف', readonly=True, store=True)

    #quantity suggestion based on the last order
    @api.onchange('inventory_counting')
    def _onchange_inventory_counting(self):
        for line in self:
            if line.order_id and line.product_id:
                previous_record = self.env['sale.order.history'].search([
                    ('order_id.partner_id', '=', line.order_id.partner_id.id),
                    ('product_id', '=', line.product_id.id)
                ], limit=1, order='id desc')

                if previous_record:
                    line.consumption = (previous_record.product_uom_qty) - (line.inventory_counting)
                else:
                    line.consumption = 0
                line.product_uom_qty = line.consumption
            else:
                line.consumption = 0
                line.product_uom_qty = 0



    #allow editing only product_uom_qty within ±5% of consumption
    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty_check(self):
        for line in self:
            if line.consumption:
                tolerance = line.consumption * 0.10 #changed to be 10%
                min_qty = line.consumption - tolerance
                max_qty = line.consumption + tolerance
                if not (min_qty <= line.product_uom_qty <= max_qty):
                    return {
                        'warning': {
                            'title': "Quantity Warning",
                            'message': f"Allowed range: {min_qty:.2f} to {max_qty:.2f}. Based on consumption quantites: {line.consumption:.2f}"
                        }
                    }




    # -----------------------------------------------------
    # multiplcation consumption * price
    # -----------------------------------------------------

    multiplied_field = fields.Float('Multiplied Field',compute="_compute_total_consumption_value", readonly=True, store=True)
    order_history_line = fields.One2many( 'sale.order.history', 'name', string='Order History Lines')

    @api.depends( 'consumption', 'price_unit' )
    def _compute_total_consumption_value (self):
        for line in self:
            line.multiplied_field = line.consumption * line.price_unit



