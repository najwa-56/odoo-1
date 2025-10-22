# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
import json
import werkzeug.utils
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class CustomerStatementPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super(CustomerStatementPortal, self)._prepare_home_portal_values(
            counters
        )
        if request.env.company.sh_display_customer_statement:
            values.update({"c_count": ""})
        return values

    @http.route(
        ["/my/customer_statements", "/my/customer_statements/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_customer_statements(self, **kw):
        values = self._prepare_portal_layout_values()
        partner_id = request.env.user.partner_id
        partner_id._compute_statements()
        customer_statement_ids = partner_id.sh_customer_statement_ids
        overdue_statement_ids = partner_id.sh_customer_due_statement_ids
        filtered_statement_ids = partner_id.sh_filter_customer_statement_ids
        values.update(
            {
                "customer_statement_ids": customer_statement_ids,
                "overdue_statement_ids": overdue_statement_ids,
                "filtered_statement_ids": filtered_statement_ids,
                "page_name": "sh_customer_statement_portal",
                "default_url": "/my/customer_statements",
            }
        )
        return request.render(
            "sh_account_statement.sh_customer_statement_portal", values
        )

    @http.route(
        ["/my/customer_statements/send"],
        type="http",
        auth="user",
        website=False,
        csrf=False,
    )
    def customer_statement_send(self, **post):
        dic = {}
        if post.get("customer_send_statement") == "true":
            request.env.user.partner_id.action_send_customer_statement()
            dic.update({"msg": "Statement Sent Successfully....."})
        if post.get("customer_send_overdue_statement") == "true":
            request.env.user.partner_id.action_send_customer_due_statement()
            dic.update({"msg": "Statement Sent Successfully....."})
        if post.get("customer_send_filter_statement") == "true":
            request.env.user.partner_id.action_send_filter_customer_statement()
            dic.update({"msg": "Statement Sent Successfully....."})
        return json.dumps(dic)

    @http.route(
        ["/my/customer_statements/xls"],
        type="http",
        auth="user",
        website=False,
        csrf=False,
    )
    def customer_statement_xls(self, **post):
        res = request.env.user.partner_id.action_print_customer_statement_xls()
        return werkzeug.utils.redirect(res.get("url"))

    @http.route(
        ["/my/filtered_customer_statements/xls"],
        type="http",
        auth="user",
        website=False,
        csrf=False,
    )
    def filtered_customer_statement_xls(self, **post):
        res = request.env.user.partner_id.action_print_filter_customer_statement_xls()
        return werkzeug.utils.redirect(res.get("url"))

    @http.route(
        ["/my/customer_statements_due/xls"],
        type="http",
        auth="user",
        website=False,
        csrf=False,
    )
    def customer_statement_xls_due(self, **post):
        res = request.env.user.partner_id.action_print_customer_due_statement_xls()
        return werkzeug.utils.redirect(res.get("url"))

    @http.route(
        ["/my/customer_statements/get"],
        type="http",
        auth="user",
        website=False,
        csrf=False,
    )
    def filter_customer_statement_get(self, **post):
        dic = {}
        if post.get("start_date") and post.get("end_date"):
            statement_lines = []
            start_date = datetime.datetime.strptime(
                post.get("start_date"), DEFAULT_SERVER_DATE_FORMAT
            ).date()
            end_date = datetime.datetime.strptime(
                post.get("end_date"), DEFAULT_SERVER_DATE_FORMAT
            ).date()
            request.env.user.partner_id.sh_filter_customer_statement_ids.unlink()
            account_id = request.env.user.partner_id.property_account_receivable_id.id

            move_lines = request.env["account.move.line"].search(
                [
                    ("partner_id", "=", request.env.user.partner_id.id),
                    ("date", "<", start_date),
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
                        "sh_filter_balance": balance,
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
                        ("move_type", "in", ["out_invoice", "out_refund"]),
                        ("invoice_date", ">=", start_date),
                        ("invoice_date", "<=", end_date),
                        ("state", "not in", ["draft", "cancel"]),
                    ]
                )
            )
            if moves:

                for move in moves:
                    statement_vals = {
                        "sh_account": request.env.user.partner_id.property_account_receivable_id.name,
                        "name": move.name,
                        "currency_id": move.currency_id.id,
                        "sh_filter_invoice_date": move.invoice_date,
                        "sh_filter_due_date": move.invoice_date_due,
                    }
                    if move.move_type == "out_invoice":
                        statement_vals.update(
                            {
                                "sh_filter_amount": move.amount_total,
                                "sh_filter_paid_amount": move.amount_total
                                - move.amount_residual,
                                "sh_filter_balance": move.amount_total
                                - (move.amount_total - move.amount_residual),
                            }
                        )
                    elif move.move_type == "out_refund":
                        statement_vals.update(
                            {
                                "sh_filter_amount": move.amount_total
                                - move.amount_residual,
                                "sh_filter_paid_amount": move.amount_total,
                                "sh_filter_balance": (
                                    move.amount_total - move.amount_residual
                                )
                                - move.amount_total,
                            }
                        )
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
                        ("partner_type", "in", ["customer"]),
                    ]
                )
            )
            if advanced_payments_inbound:
                for advance_payment in advanced_payments_inbound:
                    total_paid_amount = 0.0
                    if advance_payment.reconciled_invoice_ids:
                        advance_payment_amount = advance_payment.amount
                        for invoice in advance_payment.reconciled_invoice_ids:

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
                                "sh_filter_invoice_date": advance_payment.date,
                                "sh_filter_amount": 0.0,
                                "sh_filter_paid_amount": advance_payment.amount
                                - total_paid_amount,
                                "sh_filter_balance": -(
                                    advance_payment.amount - total_paid_amount
                                ),
                            }
                            statement_lines.append((0, 0, statement_vals))
                    else:
                        statement_vals = {
                            "sh_account": advance_payment.destination_account_id.name,
                            "name": advance_payment.name,
                            "currency_id": advance_payment.currency_id.id,
                            "sh_filter_invoice_date": advance_payment.date,
                            "sh_filter_amount": 0.0,
                            "sh_filter_paid_amount": advance_payment.amount,
                            "sh_filter_balance": -(advance_payment.amount),
                        }
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
                        ("partner_type", "in", ["customer"]),
                    ]
                )
            )
            if advanced_payments_outbound:
                for advance_payment in advanced_payments_outbound:
                    total_paid_amount = 0.0
                    if advance_payment.reconciled_invoice_ids:
                        advance_payment_amount = advance_payment.amount
                        for invoice in advance_payment.reconciled_invoice_ids:

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
                                "sh_filter_invoice_date": advance_payment.date,
                                "sh_filter_amount": advance_payment.amount
                                - total_paid_amount,
                                "sh_filter_paid_amount": 0.0,
                                "sh_filter_balance": advance_payment.amount
                                - total_paid_amount,
                            }
                            statement_lines.append((0, 0, statement_vals))
                    else:
                        statement_vals = {
                            "sh_account": advance_payment.destination_account_id.name,
                            "name": advance_payment.name,
                            "currency_id": advance_payment.currency_id.id,
                            "sh_filter_invoice_date": advance_payment.date,
                            "sh_filter_amount": advance_payment.amount,
                            "sh_filter_paid_amount": 0.0,
                            "sh_filter_balance": advance_payment.amount,
                        }
                        statement_lines.append((0, 0, statement_vals))

            if statement_lines:
                request.env.user.partner_id.sh_filter_customer_statement_ids = (
                    statement_lines
                )
                request.env.user.partner_id.start_date = start_date
                request.env.user.partner_id.end_date = end_date
        return json.dumps(dic)
