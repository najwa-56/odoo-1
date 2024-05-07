from odoo import api, fields, models, exceptions, _
from decimal import Decimal
import uuid


class AccountDebitNote(models.TransientModel):
    _inherit = "account.debit.note"

    # KSA-10
    reason = fields.Char(string='Reason', required=False,
                         help="Reasons as per Article 40 (paragraph 1) of KSA VAT regulations")

    def _prepare_default_values(self, move):
        res = super(AccountDebitNote, self)._prepare_default_values(move)
        res['credit_debit_reason'] = self.reason
        res['l10n_sa_invoice_type'] = move.l10n_sa_invoice_type
        res['l10n_is_self_billed_invoice'] = move.l10n_is_self_billed_invoice
        return res
