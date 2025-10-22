# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = "res.company"

    sh_customer_statement_auto_send = fields.Boolean("Customer Statement Auto Send")
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
        "mail.template", string=" Daily Mail Template"
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
        string=" Week Day",
    )
    sh_cust_weekly_statement_template_id = fields.Many2one(
        "mail.template", string=" Weekly Mail Template"
    )
    sh_cust_monthly_date = fields.Integer(" Monthly Day", default=1)
    sh_cust_monthly_end = fields.Boolean(" End of month")
    sh_cust_monthly_template_id = fields.Many2one(
        "mail.template", string=" Monthly Mail Template"
    )
    sh_cust_yearly_date = fields.Integer(" Yearly Day", default=1)
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
        string=" Month",
    )
    sh_cust_yearly_template_id = fields.Many2one(
        "mail.template", string=" Yearly Mail Template"
    )
    sh_cust_create_log_history = fields.Boolean("Customer Statement Mail Log History")

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
    )
    sh_cus_due_daily_statement_template_id = fields.Many2one(
        "mail.template", string="  Daily Mail Template"
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
        string="  Week Day",
    )
    sh_cust_due_weekly_statement_template_id = fields.Many2one(
        "mail.template", string="  Weekly Mail Template"
    )
    sh_cust_due_monthly_date = fields.Integer("  Monthly Day", default=1)
    sh_cust_due_monthly_end = fields.Boolean("  End of month")
    sh_cust_due_monthly_template_id = fields.Many2one(
        "mail.template", string="  Monthly Mail Template"
    )
    sh_cust_due_yearly_date = fields.Integer("  Yearly Day", default=1)
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
        string="  Month",
    )
    sh_cust_due_yearly_template_id = fields.Many2one(
        "mail.template", string="  Yearly Mail Template"
    )
    sh_cust_due_create_log_history = fields.Boolean(
        "Customer Overdue Statement Mail Log History"
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
    sh_display_customer_statement = fields.Boolean(
        "Show Customer Statement Menu in portal ?"
    )
    sh_display_vendor_statement = fields.Boolean(
        "Show Vendor Statement Menu in portal ?"
    )
    sh_display_due_statement = fields.Selection(
        [("due", "Only Due"), ("overdue", "Only Overdue"), ("both", "Both")],
        string="Display Due/Overdue Statements",
        default="both",
        required=True,
    )
    sh_statement_signature = fields.Boolean("Signature?", default=True)
    sh_display_message_in_chatter = fields.Boolean(
        "Display in Chatter Message?", default=True
    )
    sh_statement_pdf_in_message = fields.Boolean(
        "Send Report URL in Message?", default=True
    )
    sh_statement_url_in_message = fields.Boolean(
        "Send Statement URL in Message?", default=True
    )


class ResConfigSetting(models.TransientModel):
    _inherit = "res.config.settings"

    sh_customer_statement_auto_send = fields.Boolean(
        "Customer Statement Auto Send",
        related="company_id.sh_customer_statement_auto_send",
        readonly=False,
    )

    filter_only_unpaid_and_send_that = fields.Boolean(string = "Filter Only Unpaid, Send nothing if all invoices are paid",
    related='company_id.filter_only_unpaid_and_send_that',readonly=False)
    

    sh_customer_statement_action = fields.Selection(
        related="company_id.sh_customer_statement_action",
        string="Customer Statement Action",
        readonly=False,
    )
    sh_cus_daily_statement_template_id = fields.Many2one(
        "mail.template",
        string=" Daily Mail Template",
        related="company_id.sh_cus_daily_statement_template_id",
        readonly=False,
    )
    sh_cust_week_day = fields.Selection(
        string=" Week Day", related="company_id.sh_cust_week_day", readonly=False
    )
    sh_cust_weekly_statement_template_id = fields.Many2one(
        "mail.template",
        string=" Weekly Mail Template",
        related="company_id.sh_cust_weekly_statement_template_id",
        readonly=False,
    )
    sh_cust_monthly_date = fields.Integer(
        " Monthly Day",
        related="company_id.sh_cust_monthly_date",
        readonly=False,
        default=1,
    )
    sh_cust_monthly_template_id = fields.Many2one(
        "mail.template",
        string=" Monthly Mail Template",
        related="company_id.sh_cust_monthly_template_id",
        readonly=False,
    )
    sh_cust_yearly_date = fields.Integer(
        " Yearly Day",
        related="company_id.sh_cust_yearly_date",
        readonly=False,
        default=1,
    )
    sh_cust_monthly_end = fields.Boolean(
        " End of month", related="company_id.sh_cust_monthly_end", readonly=False
    )
    sh_cust_yearly_month = fields.Selection(
        string=" Month", related="company_id.sh_cust_yearly_month", readonly=False
    )
    sh_cust_yearly_template_id = fields.Many2one(
        "mail.template",
        string=" Yearly Mail Template",
        related="company_id.sh_cust_yearly_template_id",
        readonly=False,
    )
    sh_cust_create_log_history = fields.Boolean(
        "Customer Statement Mail Log History",
        related="company_id.sh_cust_create_log_history",
        readonly=False,
    )

    sh_customer_due_statement_auto_send = fields.Boolean(
        "Customer Overdue Statement Auto Send",
        related="company_id.sh_customer_due_statement_auto_send",
        readonly=False,
    )
    sh_customer_due_statement_action = fields.Selection(
        related="company_id.sh_customer_due_statement_action",
        string="Customer Overdue Statement Action",
        readonly=False,
    )
    sh_cus_due_daily_statement_template_id = fields.Many2one(
        "mail.template",
        string="  Daily Mail Template",
        related="company_id.sh_cus_due_daily_statement_template_id",
        readonly=False,
    )
    sh_cust_due_week_day = fields.Selection(
        string="  Week Day", related="company_id.sh_cust_due_week_day", readonly=False
    )
    sh_cust_due_weekly_statement_template_id = fields.Many2one(
        "mail.template",
        string="  Weekly Mail Template",
        related="company_id.sh_cust_due_weekly_statement_template_id",
        readonly=False,
    )
    sh_cust_due_monthly_date = fields.Integer(
        "  Monthly Day",
        related="company_id.sh_cust_due_monthly_date",
        readonly=False,
        default=1,
    )
    sh_cust_due_monthly_end = fields.Boolean(
        "  End of month", related="company_id.sh_cust_due_monthly_end", readonly=False
    )
    sh_cust_due_monthly_template_id = fields.Many2one(
        "mail.template",
        string="  Monthly Mail Template",
        related="company_id.sh_cust_due_monthly_template_id",
        readonly=False,
    )
    sh_cust_due_yearly_date = fields.Integer(
        "  Yearly Day",
        related="company_id.sh_cust_due_yearly_date",
        readonly=False,
        default=1,
    )
    sh_cust_due_yearly_month = fields.Selection(
        string="  Month", related="company_id.sh_cust_due_yearly_month", readonly=False
    )
    sh_cust_due_yearly_template_id = fields.Many2one(
        "mail.template",
        string="  Yearly Mail Template",
        related="company_id.sh_cust_due_yearly_template_id",
        readonly=False,
    )
    sh_cust_due_create_log_history = fields.Boolean(
        "Customer Overdue Statement Mail Log History",
        related="company_id.sh_cust_due_create_log_history",
        readonly=False,
    )

    sh_vendor_statement_auto_send = fields.Boolean(
        "Vendor Statement Auto Send",
        related="company_id.sh_vendor_statement_auto_send",
        readonly=False,
    )

    filter_only_unpaid_bill_and_send_that = fields.Boolean(string = "Filter Only Unpaid, Send nothing if all bills are paid",
    related='company_id.filter_only_unpaid_bill_and_send_that',readonly=False)

    sh_vendor_statement_action = fields.Selection(
        related="company_id.sh_vendor_statement_action",
        string="Vendor Statement Action",
        readonly=False,
    )
    sh_vend_daily_statement_template_id = fields.Many2one(
        "mail.template",
        string="Daily Mail Template ",
        related="company_id.sh_vend_daily_statement_template_id",
        readonly=False,
    )
    sh_vend_week_day = fields.Selection(
        string="Week Day ", related="company_id.sh_vend_week_day", readonly=False
    )
    sh_vend_weekly_statement_template_id = fields.Many2one(
        "mail.template",
        string="Weekly Mail Template ",
        related="company_id.sh_vend_weekly_statement_template_id",
        readonly=False,
    )
    sh_vend_monthly_date = fields.Integer(
        "Monthly Day ",
        related="company_id.sh_vend_monthly_date",
        readonly=False,
        default=1,
    )
    sh_vend_monthly_template_id = fields.Many2one(
        "mail.template",
        string="Monthly Mail Template ",
        related="company_id.sh_vend_monthly_template_id",
        readonly=False,
    )
    sh_vend_yearly_date = fields.Integer(
        "Yearly Day ",
        related="company_id.sh_vend_yearly_date",
        readonly=False,
        default=1,
    )
    sh_vend_yearly_month = fields.Selection(
        string="Month ", related="company_id.sh_vend_yearly_month", readonly=False
    )
    sh_vend_monthly_end = fields.Boolean(
        "End of month ", related="company_id.sh_vend_monthly_end", readonly=False
    )
    sh_vend_yearly_template_id = fields.Many2one(
        "mail.template",
        string="Yearly Mail Template ",
        related="company_id.sh_vend_yearly_template_id",
        readonly=False,
    )
    sh_vend_create_log_history = fields.Boolean(
        "Vendor Statement Mail Log History",
        related="company_id.sh_vend_create_log_history",
        readonly=False,
    )

    sh_vendor_due_statement_auto_send = fields.Boolean(
        "Vendor Overdue Statement Auto Send",
        related="company_id.sh_vendor_due_statement_auto_send",
        readonly=False,
    )
    sh_vendor_due_statement_action = fields.Selection(
        related="company_id.sh_vendor_due_statement_action",
        string="Vendor Overdue Statement Action",
        readonly=False,
    )
    sh_vend_due_daily_statement_template_id = fields.Many2one(
        "mail.template",
        string="Daily Mail Template",
        related="company_id.sh_vend_due_daily_statement_template_id",
        readonly=False,
    )
    sh_vend_due_week_day = fields.Selection(
        string="Week Day  ", related="company_id.sh_vend_due_week_day", readonly=False
    )
    sh_vend_due_weekly_statement_template_id = fields.Many2one(
        "mail.template",
        string="Weekly Mail Template  ",
        related="company_id.sh_vend_due_weekly_statement_template_id",
        readonly=False,
    )
    sh_vend_due_monthly_date = fields.Integer(
        "Monthly Day  ",
        related="company_id.sh_vend_due_monthly_date",
        readonly=False,
        default=1,
    )
    sh_vend_due_monthly_end = fields.Boolean(
        "End of month  ", related="company_id.sh_vend_due_monthly_end", readonly=False
    )
    sh_vend_due_monthly_template_id = fields.Many2one(
        "mail.template",
        string="Monthly Mail Template  ",
        related="company_id.sh_vend_due_monthly_template_id",
        readonly=False,
    )
    sh_vend_due_yearly_date = fields.Integer(
        "Yearly Day  ",
        related="company_id.sh_vend_due_yearly_date",
        readonly=False,
        default=1,
    )
    sh_vend_due_yearly_month = fields.Selection(
        string="Month  ", related="company_id.sh_vend_due_yearly_month", readonly=False
    )
    sh_vend_due_yearly_template_id = fields.Many2one(
        "mail.template",
        string="Yearly Mail Template  ",
        related="company_id.sh_vend_due_yearly_template_id",
        readonly=False,
    )
    sh_vend_due_create_log_history = fields.Boolean(
        "Vendor Overdue Statement Mail Log History",
        related="company_id.sh_vend_due_create_log_history",
        readonly=False,
    )
    sh_display_customer_statement = fields.Boolean(
        "Show Customer Statement Menu in portal ?",
        readonly=False,
        related="company_id.sh_display_customer_statement",
    )
    sh_display_vendor_statement = fields.Boolean(
        "Show Vendor Statement Menu in portal ?",
        readonly=False,
        related="company_id.sh_display_vendor_statement",
    )
    sh_display_due_statement = fields.Selection(
        string="Display Due/Overdue Statements",
        required=True,
        related="company_id.sh_display_due_statement",
        readonly=False,
    )
    sh_statement_signature = fields.Boolean(
        "Signature?", related="company_id.sh_statement_signature", readonly=False
    )
    sh_display_message_in_chatter = fields.Boolean(
        "Display in Chatter Message?",
        related="company_id.sh_display_message_in_chatter",
        readonly=False,
    )
    sh_statement_pdf_in_message = fields.Boolean(
        "Send Report URL in Message?",
        related="company_id.sh_statement_pdf_in_message",
        readonly=False,
    )
    sh_statement_url_in_message = fields.Boolean(
        "Send Statement URL in Message?",
        related="company_id.sh_statement_url_in_message",
        readonly=False,
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
