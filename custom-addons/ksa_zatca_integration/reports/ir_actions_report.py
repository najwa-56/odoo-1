# -*- coding: utf-8 -*-
from odoo import models


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        # EXTENDS base
        collected_streams = super()._render_qweb_pdf_prepare_streams(report_ref, data, res_ids=res_ids)

        if (collected_streams and res_ids and len(res_ids) == 1
                and self._get_report(report_ref).report_name in
                ['ksa_zatca_integration.report_e_invoicing_b2b_template', 'ksa_zatca_integration.report_e_invoicing_b2c_template']):
            invoice = self.env['account.move'].browse(res_ids)
            if invoice.is_zatca:
                collected_streams = invoice._l10n_sa_pdf_conversion(collected_streams)

        return collected_streams
