from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    total_consumption_amount_perSO = fields.Float(string='Total consumption Amount', compute='_compute_total_consumption_amount_perSO', store=True)

    @api.depends('order_line.multiplied_field')
    def _compute_total_consumption_amount_perSO(self):
        for order in self:
            order.total_consumption_amount_perSO = sum(line.multiplied_field for line in order.order_line)
