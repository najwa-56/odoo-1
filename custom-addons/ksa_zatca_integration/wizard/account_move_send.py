from odoo import models, api


class AccountMoveSend(models.TransientModel):
    _inherit = "account.move.send"

    @api.model
    def _prepare_invoice_pdf_report(self, invoice, invoice_data):
        is_tax_invoice = 1 if invoice.l10n_sa_invoice_type == 'Standard' else 0
        if invoice.invoice_pdf_report_id or not invoice.is_zatca or not invoice.zatca_invoice:
            return super()._prepare_invoice_pdf_report(invoice, invoice_data)
        if is_tax_invoice:
            report = invoice._get_zatca_invoice()[0]
        else:
            report = invoice._get_zatca_invoice()[1]
        
        content, _report_format = self.env['ir.actions.report'].with_company(invoice.company_id)._render(report, invoice.ids)
        invoice_data['pdf_attachment_values'] = {
            'raw': content,
            'name': invoice.zatca_invoice_name.replace('.xml', ''),
            'mimetype': 'application/pdf',
            'res_model': invoice._name,
            'res_id': invoice.id,
            'res_field': 'invoice_pdf_report_file', # Binary field
        }

    @api.model
    def _prepare_invoice_proforma_pdf_report(self, invoice, invoice_data):
        is_tax_invoice = 1 if invoice.l10n_sa_invoice_type == 'Standard' else 0
        if not invoice.is_zatca or not invoice.zatca_invoice:
            return super()._prepare_invoice_proforma_pdf_report(invoice, invoice_data)
        if is_tax_invoice:
            report = invoice._get_zatca_invoice()[0]
        else:
            report = invoice._get_zatca_invoice()[1]

        content, _report_format = self.env['ir.actions.report'].with_company(invoice.company_id)._render(report, invoice.ids, data={'proforma': True})

        invoice_data['proforma_pdf_attachment_values'] = {
            'raw': content,
            'name': invoice.zatca_invoice_name.replace('.xml', ''),
            'mimetype': 'application/pdf',
            'res_model': invoice._name,
            'res_id': invoice.id,
        }

    @api.model
    def _hook_invoice_document_after_pdf_report_render(self, invoice, invoice_data):
        # EXTENDS 'account'
        if not invoice.is_zatca:
            return super()._hook_invoice_document_after_pdf_report_render(invoice, invoice_data)
        return
