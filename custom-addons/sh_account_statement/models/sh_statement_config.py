# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _
import calendar
import logging

_logger = logging.getLogger(__name__)


class ShStatementConfig(models.Model):
    _name = "sh.statement.config"
    _discription = "Send Statement Configuration"

    name = fields.Char("Title")
    # customer fields
    sh_customer_partner_ids = fields.Many2many(
        "res.partner", "res_sh_customer_partner_ids", string="Customer"
    )

    sh_customer_statement_auto_send = fields.Boolean(
        "Customer Statement Auto Send", readonly=False
    )
    filter_only_unpaid_and_send_that = fields.Boolean(string = "Filter Only Unpaid, Send nothing if all invoices are paid")
    sh_customer_statement_action = fields.Selection(
        [
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("yearly", "Yearly"),
        ],
        string="Customer Statement Action",
    )
    sh_cus_daily_statement_template_id = fields.Many2one(
        "mail.template", string="  Daily Mail Template"
    )
    sh_cust_week_day = fields.Selection(
        [
            ("0", "Monday"),
            ("1", "Tuesday"),
            ("2", "Wednesday"),
            ("3", "Thursday"),
            ("4", "Friday"),
            ("5", "Saturday"),
            ("6", "Sunday"),
        ],
        string="Week Day",
        readonly=False,
    )
    sh_cust_weekly_statement_template_id = fields.Many2one(
        "mail.template", string="Weekly Mail Template   ", readonly=False
    )
    sh_cust_monthly_date = fields.Integer("Monthly  Day", readonly=False, default=1)
    sh_cust_monthly_template_id = fields.Many2one(
        "mail.template", string="Monthly Mail Template", readonly=False
    )
    sh_cust_yearly_date = fields.Integer(" Yearly day ", readonly=False, default=1)
    sh_cust_monthly_end = fields.Boolean("End of  month", readonly=False)
    sh_cust_yearly_month = fields.Selection(
        [
            ("january", "January"),
            ("february", "February"),
            ("march", "March"),
            ("april", "April"),
            ("may", "May"),
            ("june", "June"),
            ("july", "July"),
            ("august", "August"),
            ("september", "September"),
            ("october", "October"),
            ("november", "November"),
            ("december", "December"),
        ],
        string="  Month",
        readonly=False,
    )
    sh_cust_yearly_template_id = fields.Many2one(
        "mail.template", string="  Yearly Mail Template", readonly=False
    )
    sh_cust_create_log_history = fields.Boolean(
        "Customer Statement Mail Log History", readonly=False
    )

    sh_customer_due_statement_auto_send = fields.Boolean(
        "Customer Overdue Statement Auto Send"
    )
    sh_customer_due_statement_action = fields.Selection(
        [
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("yearly", "Yearly"),
        ],
        string="Customer Overdue Statement Action",
        readonly=False,
    )
    sh_cus_due_daily_statement_template_id = fields.Many2one(
        "mail.template", string=" Daily Mail Template", readonly=False
    )
    sh_cust_due_week_day = fields.Selection(
        [
            ("0", "Monday"),
            ("1", "Tuesday"),
            ("2", "Wednesday"),
            ("3", "Thursday"),
            ("4", "Friday"),
            ("5", "Saturday"),
            ("6", "Sunday"),
        ],
        string="Week Day ",
        readonly=False,
    )
    sh_cust_due_weekly_statement_template_id = fields.Many2one(
        "mail.template", string="   Weekly Mail Template", readonly=False
    )
    sh_cust_due_monthly_date = fields.Integer(
        "Monthly Day    ", readonly=False, default=1
    )
    sh_cust_due_monthly_end = fields.Boolean("End of month", readonly=False)
    sh_cust_due_monthly_template_id = fields.Many2one(
        "mail.template", string="Monthly  Mail Template", readonly=False
    )
    sh_cust_due_yearly_date = fields.Integer(
        "  Yearly Day     ", readonly=False, default=1
    )
    sh_cust_due_yearly_month = fields.Selection(
        [
            ("january", "January"),
            ("february", "February"),
            ("march", "March"),
            ("april", "April"),
            ("may", "May"),
            ("june", "June"),
            ("july", "July"),
            ("august", "August"),
            ("september", "September"),
            ("october", "October"),
            ("november", "November"),
            ("december", "December"),
        ],
        string="Month",
        readonly=False,
    )
    sh_cust_due_yearly_template_id = fields.Many2one(
        "mail.template", string=" Yearly Mail Template", readonly=False
    )
    sh_cust_due_create_log_history = fields.Boolean(
        "Customer Overdue Statement Mail Log History", readonly=False
    )

    # vendor fields
    sh_vendor_partner_ids = fields.Many2many(
        "res.partner", "res_sh_vendor_partner_ids", string="Vendor"
    )

    sh_vendor_statement_auto_send = fields.Boolean("Vendor Statement Auto Send")
    filter_only_unpaid_bill_and_send_that = fields.Boolean(string = "Filter Only Unpaid Bills, Send nothing if all bills are paid")
    sh_vendor_statement_action = fields.Selection(
        [
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("yearly", "Yearly"),
        ],
        string="Vendor Statement Action",
    )
    sh_vend_daily_statement_template_id = fields.Many2one(
        "mail.template", string="Daily Mail Template "
    )
    sh_vend_week_day = fields.Selection(
        [
            ("0", "Monday"),
            ("1", "Tuesday"),
            ("2", "Wednesday"),
            ("3", "Thursday"),
            ("4", "Friday"),
            ("5", "Saturday"),
            ("6", "Sunday"),
        ],
        string="Week Day ",
    )
    sh_vend_weekly_statement_template_id = fields.Many2one(
        "mail.template", string="Weekly Mail Template "
    )
    sh_vend_monthly_date = fields.Integer("Monthly Day ", default=1)
    sh_vend_monthly_end = fields.Boolean("End of month ")
    sh_vend_monthly_template_id = fields.Many2one(
        "mail.template", string="Monthly Mail Template "
    )
    sh_vend_yearly_date = fields.Integer("Yearly Day ", default=1)
    sh_vend_yearly_month = fields.Selection(
        [
            ("january", "January"),
            ("february", "February"),
            ("march", "March"),
            ("april", "April"),
            ("may", "May"),
            ("june", "June"),
            ("july", "July"),
            ("august", "August"),
            ("september", "September"),
            ("october", "October"),
            ("november", "November"),
            ("december", "December"),
        ],
        string="Month ",
    )
    sh_vend_yearly_template_id = fields.Many2one(
        "mail.template", string="Yearly Mail Template "
    )
    sh_vend_create_log_history = fields.Boolean("Vendor Statement Mail Log History")

    sh_vendor_due_statement_auto_send = fields.Boolean(
        "Vendor Overdue Statement Auto Send"
    )
    sh_vendor_due_statement_action = fields.Selection(
        [
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("yearly", "Yearly"),
        ],
        string="Vendor Overdue Statement Action",
    )
    sh_vend_due_daily_statement_template_id = fields.Many2one(
        "mail.template", string="Daily Mail Template  "
    )
    sh_vend_due_week_day = fields.Selection(
        [
            ("0", "Monday"),
            ("1", "Tuesday"),
            ("2", "Wednesday"),
            ("3", "Thursday"),
            ("4", "Friday"),
            ("5", "Saturday"),
            ("6", "Sunday"),
        ],
        string="Week Day  ",
    )
    sh_vend_due_weekly_statement_template_id = fields.Many2one(
        "mail.template", string="Weekly Mail Template  "
    )
    sh_vend_due_monthly_date = fields.Integer("Monthly Day  ", default=1)
    sh_vend_due_monthly_end = fields.Boolean("End of month  ")
    sh_vend_due_monthly_template_id = fields.Many2one(
        "mail.template", string="Monthly Mail Template  "
    )
    sh_vend_due_yearly_date = fields.Integer("Yearly Day  ", default=1)
    sh_vend_due_yearly_month = fields.Selection(
        [
            ("january", "January"),
            ("february", "February"),
            ("march", "March"),
            ("april", "April"),
            ("may", "May"),
            ("june", "June"),
            ("july", "July"),
            ("august", "August"),
            ("september", "September"),
            ("october", "October"),
            ("november", "November"),
            ("december", "December"),
        ],
        string="Month  ",
    )
    sh_vend_due_yearly_template_id = fields.Many2one(
        "mail.template", string="Yearly Mail Template  "
    )
    sh_vend_due_create_log_history = fields.Boolean(
        "Vendor Overdue Statement Mail Log History"
    )

    @api.onchange("sh_customer_statement_auto_send")
    def onchange_sh_customer_statement_auto_send(self):
        if not self.sh_customer_statement_auto_send:
            self.sh_customer_statement_action = False
            self.sh_cus_daily_statement_template_id = False
            self.sh_cust_week_day = False
            self.sh_cust_weekly_statement_template_id = False
            self.sh_cust_monthly_date = 0
            self.sh_cust_monthly_template_id = False
            self.sh_cust_yearly_date = 0
            self.sh_cust_yearly_month = False
            self.sh_cust_yearly_template_id = False
            self.sh_cust_monthly_end = False

    @api.onchange("sh_customer_due_statement_auto_send")
    def onchange_sh_customer_due_statement_auto_send(self):
        if not self.sh_customer_due_statement_auto_send:
            self.sh_customer_due_statement_action = False
            self.sh_cus_due_daily_statement_template_id = False
            self.sh_cust_due_week_day = False
            self.sh_cust_due_weekly_statement_template_id = False
            self.sh_cust_due_monthly_date = 0
            self.sh_cust_due_monthly_template_id = False
            self.sh_cust_due_yearly_date = 0
            self.sh_cust_due_yearly_month = False
            self.sh_cust_due_yearly_template_id = False
            self.sh_cust_due_monthly_end = False

    @api.onchange("sh_vendor_statement_auto_send")
    def onchange_sh_vendor_statement_auto_send(self):
        if not self.sh_vendor_statement_auto_send:
            self.sh_vendor_statement_action = False
            self.sh_vend_daily_statement_template_id = False
            self.sh_vend_week_day = False
            self.sh_vend_weekly_statement_template_id = False
            self.sh_vend_monthly_date = 0
            self.sh_vend_monthly_template_id = False
            self.sh_vend_yearly_date = 0
            self.sh_vend_yearly_month = False
            self.sh_vend_yearly_template_id = False
            self.sh_vend_monthly_end = False

    @api.onchange("sh_vendor_due_statement_auto_send")
    def onchange_sh_vendor_due_statement_auto_send(self):
        if not self.sh_vendor_due_statement_auto_send:
            self.sh_vendor_due_statement_action = False
            self.sh_vend_due_daily_statement_template_id = False
            self.sh_vend_due_week_day = False
            self.sh_vend_due_weekly_statement_template_id = False
            self.sh_vend_due_monthly_date = 0
            self.sh_vend_due_monthly_template_id = False
            self.sh_vend_due_yearly_date = 0
            self.sh_vend_due_yearly_month = False
            self.sh_vend_due_yearly_template_id = False
            self.sh_vend_due_monthly_end = False

    # mail history form button
    def mail_history(self):
        search = (
            self.env["sh.partner.mail.history"]
            .search(
                [
                    "|",
                    ("sh_partner_id", "in", self.sh_customer_partner_ids.ids),
                    ("sh_partner_id", "in", (self.sh_vendor_partner_ids.ids)),
                ]
            )
            .ids
        )
        return {
            "name": _("Mail Log History"),
            "type": "ir.actions.act_window",
            "view_type": "list",
            "view_mode": "list,form",
            "res_model": "sh.partner.mail.history",
            "domain": [("id", "in", search)],
        }

    # mass action wizard
    def add_replace_partner_manually_(self):
        view = self.env.ref("sh_account_statement.sh_update_partners_statement_wizard")
        return {
            "name": "Mass Update",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "views": [(view.id, "form")],
            "res_model": "sh.partners.mass.update",
            "view_id": view.id,
            "target": "new",
            "context": {"default_sh_statement_ids": self.ids},
        }

    @api.model
    def create(self, vals):
        res = super(ShStatementConfig, self).create(vals)
        if res.sh_customer_partner_ids:
            for rec in res.sh_customer_partner_ids:
                rec.sh_customer_statement_config = [(4, res.id)]
        if res.sh_vendor_partner_ids:
            for rec in res.sh_vendor_partner_ids:
                rec.sh_vendor_statement_config = [(4, res.id)]
        return res

    def write(self, vals):
        res = super(ShStatementConfig, self).write(vals)
        if self.sh_customer_partner_ids:
            for k in self.sh_customer_partner_ids:
                k.sh_customer_statement_config = [(4, self.id)]
        if self.sh_vendor_partner_ids:
            for j in self.sh_vendor_partner_ids:
                j.sh_vendor_statement_config = [(4, self.id)]
        return res

    @api.model
    def _run_auto_send_config_statements(self):
        statements_ids = self.env["sh.statement.config"].sudo().search([])
        for statement in statements_ids:
            try:
                # for customer
                for partner in statement.sh_customer_partner_ids:
                    if partner.customer_rank > 0:
                        # for statement
                        if not partner.sh_dont_send_statement_auto:
                            
                            if statement.sh_customer_statement_auto_send:
                                if statement.filter_only_unpaid_and_send_that and not partner.sh_customer_statement_ids.filtered(lambda x:x.sh_customer_balance > 0):
                                    return

                            if (
                                statement.sh_customer_statement_auto_send
                                and partner.sh_customer_statement_ids
                            ):
                                if statement.sh_customer_statement_action == "daily":
                                    if statement.sh_cus_daily_statement_template_id:
                                        mail = statement.sh_cus_daily_statement_template_id.sudo().send_mail(
                                            partner.id, force_send=True
                                        )
                                        mail_id = (
                                            self.env["mail.mail"].sudo().browse(mail)
                                        )
                                        if (
                                            mail_id
                                            and statement.sh_cust_create_log_history
                                        ):
                                            self.env[
                                                "sh.partner.mail.history"
                                            ].sudo().create(
                                                {
                                                    "name": "Customer Account Statement",
                                                    "sh_statement_type": "customer_statement",
                                                    "sh_current_date": fields.Datetime.now(),
                                                    "sh_partner_id": partner.id,
                                                    "sh_mail_id": mail_id.id,
                                                    "sh_mail_status": mail_id.state,
                                                }
                                            )
                                elif statement.sh_customer_statement_action == "weekly":
                                    today = fields.Date.today().weekday()
                                    if int(statement.sh_cust_week_day) == today:
                                        if (
                                            statement.sh_cust_weekly_statement_template_id
                                        ):
                                            mail = statement.sh_cust_weekly_statement_template_id.sudo().send_mail(
                                                partner.id, force_send=True
                                            )
                                            mail_id = (
                                                self.env["mail.mail"]
                                                .sudo()
                                                .browse(mail)
                                            )
                                            if (
                                                mail_id
                                                and statement.sh_cust_create_log_history
                                            ):
                                                self.env[
                                                    "sh.partner.mail.history"
                                                ].sudo().create(
                                                    {
                                                        "name": "Customer Account Statement",
                                                        "sh_statement_type": "customer_statement",
                                                        "sh_current_date": fields.Datetime.now(),
                                                        "sh_partner_id": partner.id,
                                                        "sh_mail_id": mail_id.id,
                                                        "sh_mail_status": mail_id.state,
                                                    }
                                                )
                                elif (
                                    statement.sh_customer_statement_action == "monthly"
                                ):
                                    monthly_day = statement.sh_cust_monthly_date
                                    today = fields.Date.today()
                                    today_date = today.day
                                    if statement.sh_cust_monthly_end:
                                        last_day = calendar.monthrange(
                                            today.year, today.month
                                        )[1]
                                        if today_date == last_day:
                                            if statement.sh_cust_monthly_template_id:
                                                mail = statement.sh_cust_monthly_template_id.sudo().send_mail(
                                                    partner.id, force_send=True
                                                )
                                                mail_id = (
                                                    self.env["mail.mail"]
                                                    .sudo()
                                                    .browse(mail)
                                                )
                                                if (
                                                    mail_id
                                                    and statement.sh_cust_create_log_history
                                                ):
                                                    self.env[
                                                        "sh.partner.mail.history"
                                                    ].sudo().create(
                                                        {
                                                            "name": "Customer Account Statement",
                                                            "sh_statement_type": "customer_statement",
                                                            "sh_current_date": fields.Datetime.now(),
                                                            "sh_partner_id": partner.id,
                                                            "sh_mail_id": mail_id.id,
                                                            "sh_mail_status": mail_id.state,
                                                        }
                                                    )
                                    else:
                                        if today_date == monthly_day:
                                            if statement.sh_cust_monthly_template_id:
                                                mail = statement.sh_cust_monthly_template_id.sudo().send_mail(
                                                    partner.id, force_send=True
                                                )
                                                mail_id = (
                                                    self.env["mail.mail"]
                                                    .sudo()
                                                    .browse(mail)
                                                )
                                                if (
                                                    mail_id
                                                    and statement.sh_cust_create_log_history
                                                ):
                                                    self.env[
                                                        "sh.partner.mail.history"
                                                    ].sudo().create(
                                                        {
                                                            "name": "Customer Account Statement",
                                                            "sh_statement_type": "customer_statement",
                                                            "sh_current_date": fields.Datetime.now(),
                                                            "sh_partner_id": partner.id,
                                                            "sh_mail_id": mail_id.id,
                                                            "sh_mail_status": mail_id.state,
                                                        }
                                                    )
                                elif statement.sh_customer_statement_action == "yearly":
                                    today = fields.Date.today()
                                    today_date = today.day
                                    today_month = today.strftime("%B").lower()
                                    if (
                                        statement.sh_cust_yearly_date == today_date
                                        and statement.sh_cust_yearly_month
                                        == today_month
                                    ):
                                        if statement.sh_cust_yearly_template_id:
                                            mail = statement.sh_cust_yearly_template_id.sudo().send_mail(
                                                partner.id, force_send=True
                                            )
                                            mail_id = (
                                                self.env["mail.mail"]
                                                .sudo()
                                                .browse(mail)
                                            )
                                            if (
                                                mail_id
                                                and statement.sh_cust_create_log_history
                                            ):
                                                self.env[
                                                    "sh.partner.mail.history"
                                                ].sudo().create(
                                                    {
                                                        "name": "Customer Account Statement",
                                                        "sh_statement_type": "customer_statement",
                                                        "sh_current_date": fields.Datetime.now(),
                                                        "sh_partner_id": partner.id,
                                                        "sh_mail_id": mail_id.id,
                                                        "sh_mail_status": mail_id.state,
                                                    }
                                                )
                        # for overdue statement
                        if not partner.sh_dont_send_due_statement_auto:
                            if (
                                statement.sh_customer_due_statement_auto_send
                                and partner.sh_customer_due_statement_ids
                            ):
                                if statement.filter_only_unpaid_and_send_that and not partner.sh_customer_due_statement_ids.filtered(lambda x:x.sh_due_customer_balance > 0):
                                    return
                                
                                if (
                                    statement.sh_customer_due_statement_action
                                    == "daily"
                                ):
                                    if statement.sh_cus_due_daily_statement_template_id:
                                        mail = statement.sh_cus_due_daily_statement_template_id.sudo().send_mail(
                                            partner.id, force_send=True
                                        )
                                        mail_id = (
                                            self.env["mail.mail"].sudo().browse(mail)
                                        )
                                        if (
                                            mail_id
                                            and statement.sh_cust_due_create_log_history
                                        ):
                                            self.env[
                                                "sh.partner.mail.history"
                                            ].sudo().create(
                                                {
                                                    "name": "Customer Account Overdue Statement",
                                                    "sh_statement_type": "customer_overdue_statement",
                                                    "sh_current_date": fields.Datetime.now(),
                                                    "sh_partner_id": partner.id,
                                                    "sh_mail_id": mail_id.id,
                                                    "sh_mail_status": mail_id.state,
                                                }
                                            )
                                elif (
                                    statement.sh_customer_due_statement_action
                                    == "weekly"
                                ):
                                    today = fields.Date.today().weekday()
                                    if int(statement.sh_cust_due_week_day) == today:
                                        if (
                                            statement.sh_cust_due_weekly_statement_template_id
                                        ):
                                            mail = statement.sh_cust_due_weekly_statement_template_id.sudo().send_mail(
                                                partner.id, force_send=True
                                            )
                                            mail_id = (
                                                self.env["mail.mail"]
                                                .sudo()
                                                .browse(mail)
                                            )
                                            if (
                                                mail_id
                                                and statement.sh_cust_due_create_log_history
                                            ):
                                                self.env[
                                                    "sh.partner.mail.history"
                                                ].sudo().create(
                                                    {
                                                        "name": "Customer Account Overdue Statement",
                                                        "sh_statement_type": "customer_overdue_statement",
                                                        "sh_current_date": fields.Datetime.now(),
                                                        "sh_partner_id": partner.id,
                                                        "sh_mail_id": mail_id.id,
                                                        "sh_mail_status": mail_id.state,
                                                    }
                                                )
                                elif (
                                    statement.sh_customer_due_statement_action
                                    == "monthly"
                                ):
                                    monthly_day = statement.sh_cust_due_monthly_date
                                    today = fields.Date.today()
                                    today_date = today.day
                                    if statement.sh_cust_due_monthly_end:
                                        last_day = calendar.monthrange(
                                            today.year, today.month
                                        )[1]
                                        if today_date == last_day:
                                            if (
                                                statement.sh_cust_due_monthly_template_id
                                            ):
                                                mail = statement.sh_cust_due_monthly_template_id.sudo().send_mail(
                                                    partner.id, force_send=True
                                                )
                                                mail_id = (
                                                    self.env["mail.mail"]
                                                    .sudo()
                                                    .browse(mail)
                                                )
                                                if (
                                                    mail_id
                                                    and statement.sh_cust_due_create_log_history
                                                ):
                                                    self.env[
                                                        "sh.partner.mail.history"
                                                    ].sudo().create(
                                                        {
                                                            "name": "Customer Account Overdue Statement",
                                                            "sh_statement_type": "customer_overdue_statement",
                                                            "sh_current_date": fields.Datetime.now(),
                                                            "sh_partner_id": partner.id,
                                                            "sh_mail_id": mail_id.id,
                                                            "sh_mail_status": mail_id.state,
                                                        }
                                                    )
                                    else:
                                        if today_date == monthly_day:
                                            if (
                                                statement.sh_cust_due_monthly_template_id
                                            ):
                                                mail = statement.sh_cust_due_monthly_template_id.sudo().send_mail(
                                                    partner.id, force_send=True
                                                )
                                                mail_id = (
                                                    self.env["mail.mail"]
                                                    .sudo()
                                                    .browse(mail)
                                                )
                                                if (
                                                    mail_id
                                                    and statement.sh_cust_due_create_log_history
                                                ):
                                                    self.env[
                                                        "sh.partner.mail.history"
                                                    ].sudo().create(
                                                        {
                                                            "name": "Customer Account Overdue Statement",
                                                            "sh_statement_type": "customer_overdue_statement",
                                                            "sh_current_date": fields.Datetime.now(),
                                                            "sh_partner_id": partner.id,
                                                            "sh_mail_id": mail_id.id,
                                                            "sh_mail_status": mail_id.state,
                                                        }
                                                    )

                                elif (
                                    statement.sh_customer_due_statement_action
                                    == "yearly"
                                ):
                                    today = fields.Date.today()
                                    today_date = today.day
                                    today_month = today.strftime("%B").lower()
                                    if (
                                        statement.sh_cust_due_yearly_date == today_date
                                        and statement.sh_cust_due_yearly_month
                                        == today_month
                                    ):
                                        if statement.sh_cust_due_yearly_template_id:
                                            mail = statement.sh_cust_due_yearly_template_id.sudo().send_mail(
                                                partner.id, force_send=True
                                            )
                                            mail_id = (
                                                self.env["mail.mail"]
                                                .sudo()
                                                .browse(mail)
                                            )
                                            if (
                                                mail_id
                                                and statement.sh_cust_due_create_log_history
                                            ):
                                                self.env[
                                                    "sh.partner.mail.history"
                                                ].sudo().create(
                                                    {
                                                        "name": "Customer Account Overdue Statement",
                                                        "sh_statement_type": "customer_overdue_statement",
                                                        "sh_current_date": fields.Datetime.now(),
                                                        "sh_partner_id": partner.id,
                                                        "sh_mail_id": mail_id.id,
                                                        "sh_mail_status": mail_id.state,
                                                    }
                                                )
                # for Vendor
                for partner in statement.sh_vendor_partner_ids:
                    if partner.supplier_rank > 0:
                        # for statement
                        if not partner.sh_dont_send_statement_auto:
                            if (
                                statement.sh_vendor_statement_auto_send
                                and partner.sh_vendor_statement_ids
                            ):
                                if statement.filter_only_unpaid_bill_and_send_that and not partner.sh_vendor_statement_ids.filtered(lambda x:x.sh_vendor_balance > 0):
                                    return
                                
                                if statement.sh_vendor_statement_action == "daily":
                                    if statement.sh_vend_daily_statement_template_id:
                                        mail = statement.sh_vend_daily_statement_template_id.sudo().send_mail(
                                            partner.id, force_send=True
                                        )
                                        mail_id = (
                                            self.env["mail.mail"].sudo().browse(mail)
                                        )
                                        if (
                                            mail_id
                                            and statement.sh_vend_create_log_history
                                        ):
                                            self.env[
                                                "sh.partner.mail.history"
                                            ].sudo().create(
                                                {
                                                    "name": "Vendor Account Statement",
                                                    "sh_statement_type": "vendor_statement",
                                                    "sh_current_date": fields.Datetime.now(),
                                                    "sh_partner_id": partner.id,
                                                    "sh_mail_id": mail_id.id,
                                                    "sh_mail_status": mail_id.state,
                                                }
                                            )
                                elif statement.sh_vendor_statement_action == "weekly":
                                    today = fields.Date.today().weekday()
                                    if int(statement.sh_vend_week_day) == today:
                                        if (
                                            statement.sh_vend_weekly_statement_template_id
                                        ):
                                            mail = statement.sh_vend_weekly_statement_template_id.sudo().send_mail(
                                                partner.id, force_send=True
                                            )
                                            mail_id = (
                                                self.env["mail.mail"]
                                                .sudo()
                                                .browse(mail)
                                            )
                                            if (
                                                mail_id
                                                and statement.sh_vend_create_log_history
                                            ):
                                                self.env[
                                                    "sh.partner.mail.history"
                                                ].sudo().create(
                                                    {
                                                        "name": "Vendor Account Statement",
                                                        "sh_statement_type": "vendor_statement",
                                                        "sh_current_date": fields.Datetime.now(),
                                                        "sh_partner_id": partner.id,
                                                        "sh_mail_id": mail_id.id,
                                                        "sh_mail_status": mail_id.state,
                                                    }
                                                )
                                elif statement.sh_vendor_statement_action == "monthly":
                                    monthly_day = statement.sh_vend_monthly_date
                                    today = fields.Date.today()
                                    today_date = today.day
                                    if statement.sh_vend_monthly_end:
                                        last_day = calendar.monthrange(
                                            today.year, today.month
                                        )[1]
                                        if today_date == last_day:
                                            if statement.sh_vend_monthly_template_id:
                                                mail = statement.sh_vend_monthly_template_id.sudo().send_mail(
                                                    partner.id, force_send=True
                                                )
                                                mail_id = (
                                                    self.env["mail.mail"]
                                                    .sudo()
                                                    .browse(mail)
                                                )
                                                if (
                                                    mail_id
                                                    and statement.sh_vend_create_log_history
                                                ):
                                                    self.env[
                                                        "sh.partner.mail.history"
                                                    ].sudo().create(
                                                        {
                                                            "name": "Vendor Account Statement",
                                                            "sh_statement_type": "vendor_statement",
                                                            "sh_current_date": fields.Datetime.now(),
                                                            "sh_partner_id": partner.id,
                                                            "sh_mail_id": mail_id.id,
                                                            "sh_mail_status": mail_id.state,
                                                        }
                                                    )
                                    else:
                                        if today_date == monthly_day:
                                            if statement.sh_vend_monthly_template_id:
                                                mail = statement.sh_vend_monthly_template_id.sudo().send_mail(
                                                    partner.id, force_send=True
                                                )
                                                mail_id = (
                                                    self.env["mail.mail"]
                                                    .sudo()
                                                    .browse(mail)
                                                )
                                                if (
                                                    mail_id
                                                    and statement.sh_vend_create_log_history
                                                ):
                                                    self.env[
                                                        "sh.partner.mail.history"
                                                    ].sudo().create(
                                                        {
                                                            "name": "Vendor Account Statement",
                                                            "sh_statement_type": "vendor_statement",
                                                            "sh_current_date": fields.Datetime.now(),
                                                            "sh_partner_id": partner.id,
                                                            "sh_mail_id": mail_id.id,
                                                            "sh_mail_status": mail_id.state,
                                                        }
                                                    )
                                elif statement.sh_vendor_statement_action == "yearly":
                                    today = fields.Date.today()
                                    today_date = today.day
                                    today_month = today.strftime("%B").lower()
                                    if (
                                        statement.sh_vend_yearly_date == today_date
                                        and statement.sh_vend_yearly_month
                                        == today_month
                                    ):
                                        if statement.sh_vend_yearly_template_id:
                                            mail = statement.sh_vend_yearly_template_id.sudo().send_mail(
                                                partner.id, force_send=True
                                            )
                                            mail_id = (
                                                self.env["mail.mail"]
                                                .sudo()
                                                .browse(mail)
                                            )
                                            if (
                                                mail_id
                                                and statement.sh_vend_create_log_history
                                            ):
                                                self.env[
                                                    "sh.partner.mail.history"
                                                ].sudo().create(
                                                    {
                                                        "name": "Vendor Account Statement",
                                                        "sh_statement_type": "vendor_statement",
                                                        "sh_current_date": fields.Datetime.now(),
                                                        "sh_partner_id": partner.id,
                                                        "sh_mail_id": mail_id.id,
                                                        "sh_mail_status": mail_id.state,
                                                    }
                                                )
                        # for overdue statement
                        if not partner.sh_dont_send_due_statement_auto:
                            if (
                                statement.sh_vendor_due_statement_auto_send
                                and partner.sh_vendor_due_statement_ids
                            ):
                                if statement.filter_only_unpaid_bill_and_send_that and not partner.sh_vendor_due_statement_ids.filtered(lambda x:x.sh_due_vendor_balance > 0):
                                    return

                                if statement.sh_vendor_due_statement_action == "daily":
                                    if (
                                        statement.sh_vend_due_daily_statement_template_id
                                    ):
                                        mail = statement.sh_vend_due_daily_statement_template_id.sudo().send_mail(
                                            partner.id, force_send=True
                                        )
                                        mail_id = (
                                            self.env["mail.mail"].sudo().browse(mail)
                                        )
                                        if (
                                            mail_id
                                            and statement.sh_vend_due_create_log_history
                                        ):
                                            self.env[
                                                "sh.partner.mail.history"
                                            ].sudo().create(
                                                {
                                                    "name": "Vendor Account Overdue Statement",
                                                    "sh_statement_type": "vendor_overdue_statement",
                                                    "sh_current_date": fields.Datetime.now(),
                                                    "sh_partner_id": partner.id,
                                                    "sh_mail_id": mail_id.id,
                                                    "sh_mail_status": mail_id.state,
                                                }
                                            )
                                elif (
                                    statement.sh_vendor_due_statement_action == "weekly"
                                ):
                                    today = fields.Date.today().weekday()
                                    if int(statement.sh_vend_due_week_day) == today:
                                        if (
                                            statement.sh_vend_due_weekly_statement_template_id
                                        ):
                                            mail = statement.sh_vend_due_weekly_statement_template_id.sudo().send_mail(
                                                partner.id, force_send=True
                                            )
                                            mail_id = (
                                                self.env["mail.mail"]
                                                .sudo()
                                                .browse(mail)
                                            )
                                            if (
                                                mail_id
                                                and statement.sh_vend_due_create_log_history
                                            ):
                                                self.env[
                                                    "sh.partner.mail.history"
                                                ].sudo().create(
                                                    {
                                                        "name": "Vendor Account Overdue Statement",
                                                        "sh_statement_type": "vendor_overdue_statement",
                                                        "sh_current_date": fields.Datetime.now(),
                                                        "sh_partner_id": partner.id,
                                                        "sh_mail_id": mail_id.id,
                                                        "sh_mail_status": mail_id.state,
                                                    }
                                                )
                                elif (
                                    statement.sh_vendor_due_statement_action
                                    == "monthly"
                                ):
                                    monthly_day = statement.sh_vend_due_monthly_date
                                    today = fields.Date.today()
                                    today_date = today.day
                                    if statement.sh_vend_due_monthly_end:
                                        last_day = calendar.monthrange(
                                            today.year, today.month
                                        )[1]
                                        if today_date == last_day:
                                            if (
                                                statement.sh_vend_due_monthly_template_id
                                            ):
                                                mail = statement.sh_vend_due_monthly_template_id.sudo().send_mail(
                                                    partner.id, force_send=True
                                                )
                                                mail_id = (
                                                    self.env["mail.mail"]
                                                    .sudo()
                                                    .browse(mail)
                                                )
                                                if (
                                                    mail_id
                                                    and statement.sh_vend_due_create_log_history
                                                ):
                                                    self.env[
                                                        "sh.partner.mail.history"
                                                    ].sudo().create(
                                                        {
                                                            "name": "Vendor Account Overdue Statement",
                                                            "sh_statement_type": "vendor_overdue_statement",
                                                            "sh_current_date": fields.Datetime.now(),
                                                            "sh_partner_id": partner.id,
                                                            "sh_mail_id": mail_id.id,
                                                            "sh_mail_status": mail_id.state,
                                                        }
                                                    )
                                    else:
                                        if today_date == monthly_day:
                                            if (
                                                statement.sh_vend_due_monthly_template_id
                                            ):
                                                mail = statement.sh_vend_due_monthly_template_id.sudo().send_mail(
                                                    partner.id, force_send=True
                                                )
                                                mail_id = (
                                                    self.env["mail.mail"]
                                                    .sudo()
                                                    .browse(mail)
                                                )
                                                if (
                                                    mail_id
                                                    and statement.sh_vend_due_create_log_history
                                                ):
                                                    self.env[
                                                        "sh.partner.mail.history"
                                                    ].sudo().create(
                                                        {
                                                            "name": "Vendor Account Overdue Statement",
                                                            "sh_statement_type": "vendor_overdue_statement",
                                                            "sh_current_date": fields.Datetime.now(),
                                                            "sh_partner_id": partner.id,
                                                            "sh_mail_id": mail_id.id,
                                                            "sh_mail_status": mail_id.state,
                                                        }
                                                    )
                                elif (
                                    statement.sh_vendor_due_statement_action == "yearly"
                                ):
                                    today = fields.Date.today()
                                    today_date = today.day
                                    today_month = today.strftime("%B").lower()
                                    if (
                                        statement.sh_vend_due_yearly_date == today_date
                                        and statement.sh_vend_due_yearly_month
                                        == today_month
                                    ):
                                        if statement.sh_vend_due_yearly_template_id:
                                            mail = statement.sh_vend_due_yearly_template_id.sudo().send_mail(
                                                partner.id, force_send=True
                                            )
                                            mail_id = (
                                                self.env["mail.mail"]
                                                .sudo()
                                                .browse(mail)
                                            )
                                            if (
                                                mail_id
                                                and statement.sh_vend_due_create_log_history
                                            ):
                                                self.env[
                                                    "sh.partner.mail.history"
                                                ].sudo().create(
                                                    {
                                                        "name": "Vendor Account Overdue Statement",
                                                        "sh_statement_type": "vendor_overdue_statement",
                                                        "sh_current_date": fields.Datetime.now(),
                                                        "sh_partner_id": partner.id,
                                                        "sh_mail_id": mail_id.id,
                                                        "sh_mail_status": mail_id.state,
                                                    }
                                                )
            except Exception as e:
                _logger.error("%s", e)
