# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
import json
import werkzeug.utils
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class VendorStatementPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super(VendorStatementPortal, self)._prepare_home_portal_values(
            counters
        )
        if request.env.company.sh_display_vendor_statement:
            values.update({"v_count": ""})
        return values

    @http.route(
        ["/my/vendor_statements", "/my/vendor_statements/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_vendor_statements(self, **kw):
        values = self._prepare_portal_layout_values()
        partner_id = request.env.user.partner_id
        partner_id._compute_statements()
        vendor_statement_ids = partner_id.sh_vendor_statement_ids
        vendor_overdue_statement_ids = partner_id.sh_vendor_due_statement_ids
        filtered_statement_ids = partner_id.sh_filter_vendor_statement_ids
        values.update(
            {
                "vendor_statement_ids": vendor_statement_ids,
                "vendor_overdue_statement_ids": vendor_overdue_statement_ids,
                "page_name": "sh_vendor_statement_portal",
                "default_url": "/my/vendor_statements",
                "filtered_statement_ids": filtered_statement_ids,
            }
        )
        return request.render("sh_account_statement.sh_vendor_statement_portal", values)

    @http.route(
        ["/my/vendor_statements/send"],
        type="http",
        auth="user",
        website=False,
        csrf=False,
    )
    def vendor_statement_send(self, **post):
        dic = {}
        if post.get("vendor_send_statement") == "true":
            request.env.user.partner_id.action_send_vendor_statement()
            dic.update({"msg": "Statement Sent Successfully....."})
        if post.get("vendor_send_overdue_statement") == "true":
            request.env.user.partner_id.action_send_vendor_due_statement()
            dic.update({"msg": "Statement Sent Successfully....."})
        if post.get("vendor_send_filter_statement") == "true":
            request.env.user.partner_id.action_send_filter_vendor_statement()
            dic.update({"msg": "Statement Sent Successfully....."})
        return json.dumps(dic)

    @http.route(
        ["/my/vendor_statements/xls"],
        type="http",
        auth="user",
        website=False,
        csrf=False,
    )
    def vendor_statement_xls(self, **post):
        res = request.env.user.partner_id.action_print_vendor_statement_xls()
        return werkzeug.utils.redirect(res.get("url"))

    @http.route(
        ["/my/filtered_vendor_statements/xls"],
        type="http",
        auth="user",
        website=False,
        csrf=False,
    )
    def filtered_vendor_statement_xls(self, **post):
        res = request.env.user.partner_id.action_print_filter_vendor_statement_xls()
        return werkzeug.utils.redirect(res.get("url"))

    @http.route(
        ["/my/vendor_statements_due/xls"],
        type="http",
        auth="user",
        website=False,
        csrf=False,
    )
    def vendor_statement_xls_due(self, **post):
        res = request.env.user.partner_id.action_print_vendor_due_statement_xls()
        return werkzeug.utils.redirect(res.get("url"))

    @http.route(
        ["/my/vendor_statements/get"],
        type="http",
        auth="user",
        website=False,
        csrf=False,
    )
    def filter_vendor_statement_get(self, **post):
        dic = {}
        if post.get("start_date") and post.get("end_date"):
            statement_lines = []
            start_date = datetime.datetime.strptime(
                post.get("start_date"), DEFAULT_SERVER_DATE_FORMAT
            ).date()
            end_date = datetime.datetime.strptime(
                post.get("end_date"), DEFAULT_SERVER_DATE_FORMAT
            ).date()
            request.env.user.partner_id.sh_filter_vendor_statement_ids.unlink()
            account_id = request.env.user.partner_id.property_account_payable_id.id

            move_lines = request.env["account.move.line"].search(
                [
                    ("partner_id", "=", request.env.user.partner_id.id),
                    ("date", "<", request.env.user.partner_id.start_date),
                    ("account_id", "=", account_id),
                    ("parent_state", "=", "posted"),
                ]
            )

            balance = sum(move_lines.mapped("debit")) - sum(move_lines.mapped("credit"))

            statement_lines.append(
                (
                    0,
                    0,
                    {
                        "name": "Opening Balance",
                        "currency_id": move_lines[0].currency_id.id
                        if move_lines
                        else request.env.user.partner_id.currency_id.id,
                        "sh_vendor_filter_balance": balance,
                    },
                )
            )
            #########

            moves = (
                request.env["account.move"]
                .sudo()
                .search(
                    [
                        ("partner_id", "=", request.env.user.partner_id.id),
                        ("move_type", "in", ["in_invoice", "in_refund"]),
                        ("invoice_date", ">=", start_date),
                        ("invoice_date", "<=", end_date),
                        ("state", "not in", ["draft", "cancel"]),
                    ]
                )
            )
            if moves:

                for move in moves:
                    statement_vals = {
                        "sh_account": request.env.user.partner_id.property_account_payable_id.name,
                        "name": move.name,
                        "currency_id": move.currency_id.id,
                        "sh_vendor_filter_invoice_date": move.invoice_date,
                        "sh_vendor_filter_due_date": move.invoice_date_due,
                    }
                    if move.move_type == "in_refund":
                        statement_vals.update(
                            {
                                "sh_vendor_filter_amount": move.amount_total,
                                "sh_vendor_filter_paid_amount": move.amount_total
                                - move.amount_residual,
                                "sh_vendor_filter_balance": move.amount_total
                                - (move.amount_total - move.amount_residual),
                            }
                        )
                    elif move.move_type == "in_invoice":
                        statement_vals.update(
                            {
                                "sh_vendor_filter_amount": move.amount_total
                                - move.amount_residual,
                                "sh_vendor_filter_paid_amount": move.amount_total,
                                "sh_vendor_filter_balance": (
                                    move.amount_total - move.amount_residual
                                )
                                - move.amount_total,
                            }
                        )
                    statement_lines.append((0, 0, statement_vals))

            advanced_payments_outbound = (
                request.env["account.payment"]
                .sudo()
                .search(
                    [
                        ("partner_id", "=", request.env.user.partner_id.id),
                        ("date", ">=", start_date),
                        ("date", "<=", end_date),
                        ("state", "in", ["posted"]),
                        ("payment_type", "in", ["outbound"]),
                        ("partner_type", "in", ["supplier"]),
                    ]
                )
            )
            if advanced_payments_outbound:
                for advance_payment in advanced_payments_outbound:
                    total_paid_amount = 0.0
                    if advance_payment.reconciled_bill_ids:
                        advance_payment_amount = advance_payment.amount
                        for invoice in advance_payment.reconciled_bill_ids:
                            if (
                                invoice.invoice_date >= start_date
                                and invoice.invoice_date <= end_date
                            ):

                                total_paid_amount += (
                                    invoice.amount_total - invoice.amount_residual
                                )

                        if total_paid_amount < advance_payment_amount:
                            statement_vals = {
                                "sh_account": advance_payment.destination_account_id.name,
                                "name": advance_payment.name,
                                "currency_id": advance_payment.currency_id.id,
                                "sh_vendor_filter_invoice_date": advance_payment.date,
                                "sh_vendor_filter_amount": advance_payment.amount
                                - total_paid_amount,
                                "sh_vendor_filter_paid_amount": 0.0,
                                "sh_vendor_filter_balance": (
                                    advance_payment.amount - total_paid_amount
                                ),
                            }
                            statement_lines.append((0, 0, statement_vals))
                    else:
                        statement_vals = {
                            "sh_account": advance_payment.destination_account_id.name,
                            "name": advance_payment.name,
                            "currency_id": advance_payment.currency_id.id,
                            "sh_vendor_filter_invoice_date": advance_payment.date,
                            "sh_vendor_filter_amount": advance_payment.amount,
                            "sh_vendor_filter_paid_amount": 0.0,
                            "sh_vendor_filter_balance": advance_payment.amount,
                        }
                        statement_lines.append((0, 0, statement_vals))

            advanced_payments_inbound = (
                request.env["account.payment"]
                .sudo()
                .search(
                    [
                        ("partner_id", "=", request.env.user.partner_id.id),
                        ("date", ">=", start_date),
                        ("date", "<=", end_date),
                        ("state", "in", ["posted"]),
                        ("payment_type", "in", ["inbound"]),
                        ("partner_type", "in", ["supplier"]),
                    ]
                )
            )

            if advanced_payments_inbound:
                for advance_payment in advanced_payments_inbound:
                    total_paid_amount = 0.0
                    if advance_payment.reconciled_bill_ids:
                        advance_payment_amount = advance_payment.amount
                        for invoice in advance_payment.reconciled_bill_ids:
                            if (
                                invoice.invoice_date >= start_date
                                and invoice.invoice_date <= end_date
                            ):

                                total_paid_amount += (
                                    invoice.amount_total - invoice.amount_residual
                                )

                        if total_paid_amount < advance_payment_amount:
                            statement_vals = {
                                "sh_account": advance_payment.destination_account_id.name,
                                "name": advance_payment.name,
                                "currency_id": advance_payment.currency_id.id,
                                "sh_vendor_filter_invoice_date": advance_payment.date,
                                "sh_vendor_filter_amount": 0.0,
                                "sh_vendor_filter_paid_amount": advance_payment.amount
                                - total_paid_amount,
                                "sh_vendor_filter_balance": -(
                                    advance_payment.amount - total_paid_amount
                                ),
                            }
                            statement_lines.append((0, 0, statement_vals))
                    else:
                        statement_vals = {
                            "sh_account": advance_payment.destination_account_id.name,
                            "name": advance_payment.name,
                            "currency_id": advance_payment.currency_id.id,
                            "sh_vendor_filter_invoice_date": advance_payment.date,
                            "sh_vendor_filter_amount": 0.0,
                            "sh_vendor_filter_paid_amount": advance_payment.amount,
                            "sh_vendor_filter_balance": -(advance_payment.amount),
                        }
                        statement_lines.append((0, 0, statement_vals))
            if statement_lines:
                request.env.user.partner_id.start_date = start_date
                request.env.user.partner_id.end_date = end_date
                request.env.user.partner_id.sh_filter_vendor_statement_ids = (
                    statement_lines
                )
        return json.dumps(dic)
