
from odoo import models, api, _, fields
from odoo.exceptions import UserError



class account_journal(models.Model):
    _inherit = "account.journal"

    allowes_usesr_ids = fields.Many2many('res.users', string='Allowed Users')