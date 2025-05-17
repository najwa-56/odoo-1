from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    total_consumption_amount_perSO = fields.Float(string='Total consumption Amount', compute='_compute_total_consumption_amount_perSO', store=True)

    @api.depends('order_line.multiplied_field')
    def _compute_total_consumption_amount_perSO(self):
        for order in self:
            order.total_consumption_amount_perSO = sum(line.multiplied_field for line in order.order_line)


    #---------------------------------------------------------------------------------------------------------
    #To automatically save any new sale.order created into the order_id Many2many field in daily.visit model
    #---------------------------------------------------------------------------------------------------------
    @api.model
    def create(self, vals):
        # First create the sale order normally
        order = super(SaleOrder, self).create(vals)

        # Link it to an existing Daily Visit (latest one or matching logic)
        daily_visit = self.env['daily.visit'].search([], limit=1, order="create_date desc")
        if daily_visit:
            daily_visit.order_id = [(4, order.id)]
        else:
            # Optionally create a new DailyVisit if none exists
            self.env['daily.visit'].create({
                'order_id': [(6, 0, [order.id])]
            })

        return order