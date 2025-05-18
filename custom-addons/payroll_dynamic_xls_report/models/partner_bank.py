from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class PartnerBank(models.Model):
    _name = 'res.partner.bank'
    _inherit = ['res.partner.bank','mail.thread', 'mail.activity.mixin']
    

    iban = fields.Char("IBAN", tracking=True)
    acc_number = fields.Char('Account Number', required=True, tracking=True)
    bank_id = fields.Many2one('res.bank', string='Bank', tracking=True)


