from odoo import models

class DailyVisitReportParser(models.AbstractModel):
    _name = 'report.salesman_manager.daily_visit_pdf_template'
    _description = 'Daily Visit PDF Parser'

    def _get_report_values (self, docids, data=None):
        data = data or {}
        # Prefer ids explicitly passed via data; fall back to docids/context
        ids_from_data = data.get( 'docids' ) or []
        ids = ids_from_data or docids or self.env.context.get( 'active_ids', [] )
        docs = self.env['daily.visit.report'].browse( ids )
        return {
            'doc_ids': ids,
            'doc_model': 'daily.visit.report',
            'docs': docs,
            'data': data,
        }
