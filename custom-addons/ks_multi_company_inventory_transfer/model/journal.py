
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import ValidationError, UserError


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_dolfin = fields.Boolean('Dolfin Journal')