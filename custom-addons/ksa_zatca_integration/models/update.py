from odoo import api, fields, models, exceptions, _
import logging

_zatca = logging.getLogger('Zatca Debugger for account.move :')


class ResCompanyUpdate(models.Model):
    _inherit = 'res.company'

    zatca_serial_number = fields.Char("Serial Number")


class AccountMoveUpdate(models.Model):
    _inherit = 'account.move'

    invoice_multi_currency_id = fields.Char()


class ResPartnerUpdate(models.Model):
    _inherit = 'res.partner'

    l10n_sa_is_industry_id = fields.Boolean()
