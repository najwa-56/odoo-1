from odoo import models, fields, api
from odoo.exceptions import UserError
class AccountPayment(models.Model):
    _inherit = 'account.payment'


    #once user click confirm button it should print the payment recipt
    def action_post (self):
        res = super().action_post()
        self.ensure_one()

        if self.state != 'posted':
            raise UserError( "Receipt can only be printed after the payment is posted." )

        return {
            'type': 'ir.actions.report',
            'report_name': 'account.report_payment_receipt',
            'report_type': 'qweb-pdf',
            'res_id': self.id,
        }


