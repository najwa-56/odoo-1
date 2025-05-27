from odoo import fields, models

class SelectCustomerRouteWizard(models.TransientModel):
    _name = 'select.customer.route.wizard'
    _description = 'Select Existing Customers for Route'

    customer_ids = fields.Many2many(
        'res.partner',
        string='Customers to Add',
        domain=[('location_id', '=', False)],
        help='Customers not yet assigned to any route.'
    )

    route_line_id = fields.Many2one('route.line', string='Route Line')

    def action_add_customers_to_route(self):
        for partner in self.customer_ids:
            partner.location_id = self.route_line_id.id
        return {'type': 'ir.actions.act_window_close'}
