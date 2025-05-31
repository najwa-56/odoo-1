from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    visit_id = fields.Many2one(
        'daily.visit',
        string='Visit Reference'
    )

    visit_reference = fields.Char(
        string='Visit Reference',
        related='visit_id.reference',  # Use 'visit_id.name' if your visit uses 'name'
        store=True,
        readonly=True
    )
    #-------------------------------------------------------------------------------
    #Automatically link visit_id from related sale.order if not explicitly provided.
    # ------------------------------------------------------------------------------
    @api.model
    def create(self, vals):

        visit_id = vals.get('visit_id')
        invoice_origin = vals.get('invoice_origin')

        if not visit_id and invoice_origin:
            order = self.env['sale.order'].search(
                [('name', '=', invoice_origin)],
                limit=1
            )
            if order and order.visit_id:
                vals['visit_id'] = order.visit_id.id

        return super().create(vals)
    #-------------------------------------------------------------------------------
    #Button action to navigate back to the linked visit form.
    #-------------------------------------------------------------------------------

    def action_back_to_visit(self):

        self.ensure_one()

        if not self.visit_id:
            raise UserError(_("No visit is linked to this invoice."))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Visit'),
            'res_model': 'daily.visit',
            'res_id': self.visit_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
