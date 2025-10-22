# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import _
from odoo import http
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.http import request, content_disposition
import re


class DownloadStatementReport(http.Controller):
    def _document_check_access(self, model_name, document_id, access_token=None):
        document = request.env[model_name].browse([document_id])
        document_sudo = document.sudo().exists()
        if not document_sudo:
            raise MissingError(_("This document does not exist."))
        if (
            access_token
            and document_sudo.report_token
            and access_token == document_sudo.report_token
        ):
            return document_sudo
        else:
            raise AccessError(_("Sorry, you are not allowed to access this document."))

    def _show_report(self, model, report_type, report_ref, download=False):
        if report_type not in ('html', 'pdf', 'text'):
            raise UserError(_("Invalid report type: %s", report_type))

        ReportAction = request.env['ir.actions.report'].sudo()

        if hasattr(model, 'company_id'):
            if len(model.company_id) > 1:
                raise UserError(_('Multi company reports are not supported.'))
            ReportAction = ReportAction.with_company(model.company_id)

        method_name = '_render_qweb_%s' % (report_type)
        report = getattr(ReportAction, method_name)(report_ref, list(model.ids), data={'report_type': report_type})[0]

        headers = {
            'Content-Type': 'application/pdf' if report_type == 'pdf' else 'text/html',
            'Content-Length': len(report),
        }
        if report_type == 'pdf' and download:
            filename = "%s.pdf" % (re.sub(r'\W+', '-', model._get_cfs_report_base_filename()))
            headers['Content-Disposition'] = content_disposition(filename)
        return request.make_response(report, headers=list(headers.items()))

    def _show_vfs_report(self, model, report_type, report_ref, download=False):
        if report_type not in ('html', 'pdf', 'text'):
            raise UserError(_("Invalid report type: %s", report_type))

        ReportAction = request.env['ir.actions.report'].sudo()

        if hasattr(model, 'company_id'):
            if len(model.company_id) > 1:
                raise UserError(_('Multi company reports are not supported.'))
            ReportAction = ReportAction.with_company(model.company_id)

        method_name = '_render_qweb_%s' % (report_type)
        report = getattr(ReportAction, method_name)(report_ref, list(model.ids), data={'report_type': report_type})[0]

        headers = {
            'Content-Type': 'application/pdf' if report_type == 'pdf' else 'text/html',
            'Content-Length': len(report),
        }
        if report_type == 'pdf' and download:
            filename = "%s.pdf" % (re.sub(r'\W+', '-', model._get_vfs_report_base_filename()))
            headers['Content-Disposition'] = content_disposition(filename)
        return request.make_response(report, headers=list(headers.items()))

    def _show_cs_report(self, model, report_type, report_ref, download=False):
        if report_type not in ('html', 'pdf', 'text'):
            raise UserError(_("Invalid report type: %s", report_type))

        ReportAction = request.env['ir.actions.report'].sudo()

        if hasattr(model, 'company_id'):
            if len(model.company_id) > 1:
                raise UserError(_('Multi company reports are not supported.'))
            ReportAction = ReportAction.with_company(model.company_id)

        method_name = '_render_qweb_%s' % (report_type)
        report = getattr(ReportAction, method_name)(report_ref, list(model.ids), data={'report_type': report_type})[0]

        headers = {
            'Content-Type': 'application/pdf' if report_type == 'pdf' else 'text/html',
            'Content-Length': len(report),
        }
        if report_type == 'pdf' and download:
            filename = "%s.pdf" % (re.sub(r'\W+', '-', model._get_cs_report_base_filename()))
            headers['Content-Disposition'] = content_disposition(filename)
        return request.make_response(report, headers=list(headers.items()))

    def _show_vs_report(self, model, report_type, report_ref, download=False):
        if report_type not in ('html', 'pdf', 'text'):
            raise UserError(_("Invalid report type: %s", report_type))

        ReportAction = request.env['ir.actions.report'].sudo()

        if hasattr(model, 'company_id'):
            if len(model.company_id) > 1:
                raise UserError(_('Multi company reports are not supported.'))
            ReportAction = ReportAction.with_company(model.company_id)

        method_name = '_render_qweb_%s' % (report_type)
        report = getattr(ReportAction, method_name)(report_ref, list(model.ids), data={'report_type': report_type})[0]

        headers = {
            'Content-Type': 'application/pdf' if report_type == 'pdf' else 'text/html',
            'Content-Length': len(report),
        }
        if report_type == 'pdf' and download:
            filename = "%s.pdf" % (re.sub(r'\W+', '-', model._get_vs_report_base_filename()))
            headers['Content-Disposition'] = content_disposition(filename)
        return request.make_response(report, headers=list(headers.items()))

    
    def _show_cds_report(self, model, report_type, report_ref, download=False):
        if report_type not in ('html', 'pdf', 'text'):
            raise UserError(_("Invalid report type: %s", report_type))

        ReportAction = request.env['ir.actions.report'].sudo()

        if hasattr(model, 'company_id'):
            if len(model.company_id) > 1:
                raise UserError(_('Multi company reports are not supported.'))
            ReportAction = ReportAction.with_company(model.company_id)

        method_name = '_render_qweb_%s' % (report_type)
        report = getattr(ReportAction, method_name)(report_ref, list(model.ids), data={'report_type': report_type})[0]

        headers = {
            'Content-Type': 'application/pdf' if report_type == 'pdf' else 'text/html',
            'Content-Length': len(report),
        }
        if report_type == 'pdf' and download:
            filename = "%s.pdf" % (re.sub(r'\W+', '-', model._get_cds_report_base_filename()))
            headers['Content-Disposition'] = content_disposition(filename)
        return request.make_response(report, headers=list(headers.items()))


    def _show_vds_report(self, model, report_type, report_ref, download=False):
        if report_type not in ('html', 'pdf', 'text'):
            raise UserError(_("Invalid report type: %s", report_type))

        ReportAction = request.env['ir.actions.report'].sudo()

        if hasattr(model, 'company_id'):
            if len(model.company_id) > 1:
                raise UserError(_('Multi company reports are not supported.'))
            ReportAction = ReportAction.with_company(model.company_id)

        method_name = '_render_qweb_%s' % (report_type)
        report = getattr(ReportAction, method_name)(report_ref, list(model.ids), data={'report_type': report_type})[0]

        headers = {
            'Content-Type': 'application/pdf' if report_type == 'pdf' else 'text/html',
            'Content-Length': len(report),
        }
        if report_type == 'pdf' and download:
            filename = "%s.pdf" % (re.sub(r'\W+', '-', model._get_vds_report_base_filename()))
            headers['Content-Disposition'] = content_disposition(filename)
        return request.make_response(report, headers=list(headers.items()))

    @http.route(
        ["/download/cfs/<int:statement_id>"], type="http", auth="public", website=True
    )
    def download_customer_filter_statement(
        self,
        statement_id,
        report_type=None,
        access_token=None,
        message=False,
        download=False,
        **kw
    ):
        try:
            statement_sudo = self._document_check_access(
                "res.partner", statement_id, access_token=access_token
            )
        except (AccessError, MissingError):
            return "<br/><br/><center><h1><b>Oops Invalid URL! Please check URL and try again!</b></h1></center>"
        report_type = "pdf"
        download = True
        return self._show_report(
            model=statement_sudo,
            report_type=report_type,
            report_ref="sh_account_statement.action_report_sh_customer_filtered_statement",
            download=download,
        )

    @http.route(
        ["/download/vfs/<int:statement_id>"], type="http", auth="public", website=True
    )
    def download_vendor_filter_statement(
        self,
        statement_id,
        report_type=None,
        access_token=None,
        message=False,
        download=False,
        **kw
    ):
        try:
            statement_sudo = self._document_check_access(
                "res.partner", statement_id, access_token=access_token
            )
        except (AccessError, MissingError):
            return "<br/><br/><center><h1><b>Oops Invalid URL! Please check URL and try again!</b></h1></center>"
        report_type = "pdf"
        download = True
        return self._show_vfs_report(
            model=statement_sudo,
            report_type=report_type,
            report_ref="sh_account_statement.action_report_sh_vendor_filtered_statement",
            download=download,
        )

    @http.route(
        ["/download/cs/<int:statement_id>"], type="http", auth="public", website=True
    )
    def download_customer_statement(
        self,
        statement_id,
        report_type=None,
        access_token=None,
        message=False,
        download=False,
        **kw
    ):
        try:
            statement_sudo = self._document_check_access(
                "res.partner", statement_id, access_token=access_token
            )
        except (AccessError, MissingError):
            return "<br/><br/><center><h1><b>Oops Invalid URL! Please check URL and try again!</b></h1></center>"
        report_type = "pdf"
        download = True
        return self._show_cs_report(
            model=statement_sudo,
            report_type=report_type,
            report_ref="sh_account_statement.action_report_sh_customer_statement",
            download=download,
        )

    @http.route(
        ["/download/vs/<int:statement_id>"], type="http", auth="public", website=True
    )
    def download_vendor_statement(
        self,
        statement_id,
        report_type=None,
        access_token=None,
        message=False,
        download=False,
        **kw
    ):
        try:
            statement_sudo = self._document_check_access(
                "res.partner", statement_id, access_token=access_token
            )
        except (AccessError, MissingError):
            return "<br/><br/><center><h1><b>Oops Invalid URL! Please check URL and try again!</b></h1></center>"
        report_type = "pdf"
        download = True
        return self._show_vs_report(
            model=statement_sudo,
            report_type=report_type,
            report_ref="sh_account_statement.action_report_sh_vendor_statement",
            download=download,
        )

    @http.route(
        ["/download/cds/<int:statement_id>"], type="http", auth="public", website=True
    )
    def download_customer_due_statement(
        self,
        statement_id,
        report_type=None,
        access_token=None,
        message=False,
        download=False,
        **kw
    ):
        try:
            statement_sudo = self._document_check_access(
                "res.partner", statement_id, access_token=access_token
            )
        except (AccessError, MissingError):
            return "<br/><br/><center><h1><b>Oops Invalid URL! Please check URL and try again!</b></h1></center>"
        report_type = "pdf"
        download = True
        return self._show_cds_report(
            model=statement_sudo,
            report_type=report_type,
            report_ref="sh_account_statement.action_report_sh_customer_due_statement",
            download=download,
        )

    @http.route(
        ["/download/vds/<int:statement_id>"], type="http", auth="public", website=True
    )
    def download_vendor_due_statement(
        self,
        statement_id,
        report_type=None,
        access_token=None,
        message=False,
        download=False,
        **kw
    ):
        try:
            statement_sudo = self._document_check_access(
                "res.partner", statement_id, access_token=access_token
            )
        except (AccessError, MissingError):
            return "<br/><br/><center><h1><b>Oops Invalid URL! Please check URL and try again!</b></h1></center>"
        report_type = "pdf"
        download = True
        return self._show_vds_report(
            model=statement_sudo,
            report_type=report_type,
            report_ref="sh_account_statement.action_report_sh_vendor_due_statement",
            download=download,
        )
