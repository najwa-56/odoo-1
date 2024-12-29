
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import ValidationError, UserError


class AccountMove(models.Model):
    _inherit = 'account.move'


    def action_post(self):
        res = super().action_post()
        for inv in self:
            if inv.partner_id.is_dolfin:
                journal_id = self.env['account.journal'].search([('is_dolfin','=',True)])
                print("journal_id===================",journal_id)
                if not journal_id:
                    raise UserError("No Jouranl with is_dolfin is set")
                if journal_id:
                    inv.write({
                        'journal_id':journal_id.id
                    })
        return res
