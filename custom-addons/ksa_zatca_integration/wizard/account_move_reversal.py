from odoo import fields, models


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    # KSA-10
    reason = fields.Char(string='Reason', required=0,
                         help="Reasons as per Article 40 (paragraph 1) of KSA VAT regulations")

    def _prepare_default_reversal(self, move):
        res = super(AccountMoveReversal, self)._prepare_default_reversal(move)
        res['credit_debit_reason'] = self.reason
        res['l10n_sa_invoice_type'] = move.l10n_sa_invoice_type
        res['l10n_is_self_billed_invoice'] = move.l10n_is_self_billed_invoice
        return res
