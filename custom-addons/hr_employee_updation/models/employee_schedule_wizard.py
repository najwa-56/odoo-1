# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError



class HrEmployeeScheduleByTagWizard(models.TransientModel):
    _name = "hr.employee.schedule.by.tag.wizard"
    _description = "Update Working Schedule by Tag"

    category_ids = fields.Many2many(
        "hr.employee.category",
        string="Employee Tags",
        help="Select one or more tags to fetch the corresponding employees.",
    )
    employee_ids = fields.Many2many(
        "hr.employee",
        string="Employees",
        help="Employees carrying **all** the selected tags. "
             "You can remove or add employees manually before applying.",
    )
    schedule_id = fields.Many2one(
        "resource.calendar",
        string="Working Schedule",
        required=True,
        help="The working schedule to assign to the selected employees.",
    )

    # --------------------------------------------------
    # Onchange helpers
    # --------------------------------------------------
    @api.onchange("category_ids")
    def _onchange_category_ids(self):
        if self.category_ids:
            employees = self.env["hr.employee"].search(
                [("category_ids", "in", self.category_ids.ids)]
            )
            # Keep unique employees (search already guarantees uniqueness)
            self.employee_ids = [(6, 0, employees.ids)]
        else:
            self.employee_ids = [(5, 0, 0)]

    # --------------------------------------------------
    # Button action
    # --------------------------------------------------
    def action_apply(self):
        self.ensure_one()
        if not self.employee_ids:
            raise UserError(_("Please select at least one employee."))

        self.employee_ids.write({"resource_calendar_id": self.schedule_id.id})

        Contract = self.env["hr.contract"]
        contracts_to_update = Contract.search([
            ("employee_id", "in", self.employee_ids.ids), ("state", "=", "open"),  
                
        ])
        contracts_to_update.write({"resource_calendar_id": self.schedule_id.id})

        message = _(
            "%d employee(s) now follow the '%s' working schedule."
        ) % (len(self.employee_ids), self.schedule_id.name)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Working Schedule Updated"),
                "message": message,
                "type": "success",
                "sticky": False,
            },
            # after the toast, execute this action ⬇
            "next": {"type": "ir.actions.act_window_close"},
        }

  