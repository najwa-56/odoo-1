from odoo import api, models, _
from odoo.exceptions import ValidationError


class ReportSimplifiedTaxInvoice(models.AbstractModel):
    _name = 'report.electronic_invoice.report_simplified_tax_invoice'

    @api.model
    def _get_report_values(self, docids, data=None):
        move_id = self.env['account.move'].browse(docids)
        if move_id.partner_id.company_type != 'person':
            raise ValidationError(_("You can't print this report because type is not Individual!"))
        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': move_id,
        }
