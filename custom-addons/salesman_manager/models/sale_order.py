from odoo import models, fields, api
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    visit_id = fields.Many2one( 'daily.visit', string='Visit Reference' )
    visit_reference = fields.Char( string='Visit Reference', related='visit_id.reference', store=True )

    # ---------------------------------------------------------------------------------------------------------
    # Button action to navigate back to the linked visit form.
    # ---------------------------------------------------------------------------------------------------------
    def action_back_to_visit (self):
        self.ensure_one()
        if not self.visit_id:
            raise UserError( "No visit is linked to this sale order." )
        return {
            'type': 'ir.actions.act_window',
            'name': 'Visit',
            'res_model': 'daily.visit',
            'res_id': self.visit_id.id,
            'view_mode': 'form',
            'target': 'current',
        }


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




