# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta

APPROVED_ALLOC_STATES = ("validate", "validate1")   # allocations considered approved
APPROVED_LEAVE_STATES = ("validate", "validate1")   # leaves considered approved

class HrLeaveCarryOver(models.TransientModel):
    _name = "hr.leave.carryover.wizard"
    _description = "Carry Emergency remaining into same-date Annual allocation"

    # -------------------- helpers --------------------
    def _safe_sum(self, records, field_name):
        vals = records.mapped(field_name)
        return float(sum(v for v in vals if v))

    def _remaining_from_report(self, employee, leave_type):
        """Prefer remaining from your Balance report if present."""
        ReportModel = self.env["ir.model"]._get("report.balance.leave")
        if not ReportModel:
            return None
        Report = self.env["report.balance.leave"].sudo()
        recs = Report.search([
            ("emp_id", "=", employee.id),
            ("leave_type_id", "=", leave_type.id),
        ])
        if not recs:
            return None

        # Try common "remaining" column names
        for fname in ("remaining_balance", "remaining_days", "remaining", "remain"):
            if fname in recs._fields:
                return float(sum((r[fname] or 0.0) for r in recs))

        # Else compute from allocated - taken if those columns exist
        def first_present(record, candidates):
            for n in candidates:
                if n in record._fields:
                    return n
            return None

        alloc_f = first_present(recs[0], ["allocated_days", "allocated_balance", "allocated", "year_quota", "accrued_in_year"])
        taken_f = first_present(recs[0], ["taken_leaves", "taken_leave", "taken_in_period", "taken"])
        if alloc_f and taken_f:
            total_alloc = float(sum((r[alloc_f] or 0.0) for r in recs))
            total_taken = float(sum((r[taken_f] or 0.0) for r in recs))
            return total_alloc - total_taken
        return None

    def _remaining_from_core(self, employee, leave_type):
        Allocation = self.env["hr.leave.allocation"].sudo()
        Leave = self.env["hr.leave"].sudo()

        allocs = Allocation.search([
            ("employee_id", "=", employee.id),
            ("holiday_status_id", "=", leave_type.id),
            ("state", "in", APPROVED_ALLOC_STATES),
        ])
        total_alloc = self._safe_sum(allocs, "number_of_days")

        leaves = Leave.search([
            ("employee_id", "=", employee.id),
            ("holiday_status_id", "=", leave_type.id),
            ("state", "in", APPROVED_LEAVE_STATES),
        ])
        total_taken = self._safe_sum(leaves, "number_of_days")

        return total_alloc - total_taken

    def _remaining_for(self, employee, leave_type):
        """Remaining Emergency days (>=0)."""
        val = self._remaining_from_report(employee, leave_type)
        if val is None:
            val = self._remaining_from_core(employee, leave_type)
        return val if val > 0 else 0.0

    @api.model
    def _carry_marker_exists(self, allocation, year):
        """Prevent double-adding: look for a message we post as a marker."""
        return bool(self.env["mail.message"].sudo().search([
            ("model", "=", "hr.leave.allocation"),
            ("res_id", "=", allocation.id),
            ("body", "ilike", f"Carryover from Emergency ({year})"),
        ], limit=1))

    @api.model
    def cron_carryover_emergency_to_annual(self):
     """
     If tomorrow is the employee's anniversary (by month/day),
     add Emergency remaining to the existing Annual allocation
     whose date_from has that same month/day (year ignored).
     """
     today = fields.Date.context_today(self)
     tomorrow = today + relativedelta(days=1)
     md = (tomorrow.month, tomorrow.day)

     LeaveType = self.env["hr.leave.type"].sudo()
     Allocation = self.env["hr.leave.allocation"].sudo()
     Employee = self.env["hr.employee"].sudo()

     # all emergency types (don't rely on a single ID)
     emergency_types = LeaveType.search([("leave_kind", "=", "emergency")])

     employees = Employee.search([("active", "=", True)])
     for emp in employees:
        # find the annual allocation(s) whose date_from shares tomorrow's month/day
         annual_allocs = Allocation.search([
             ("employee_id", "=", emp.id),
             ("state", "in", APPROVED_ALLOC_STATES),
             ("date_from", "!=", False),
         ])
         annual_allocs = annual_allocs.filtered(
             lambda a: a.holiday_status_id.leave_kind == "annual"
                       and (fields.Date.to_date(a.date_from).month,
                            fields.Date.to_date(a.date_from).day) == md
         ).sorted(lambda a: a.date_from, reverse=True)
 
         if not annual_allocs:
             continue

         target_alloc = annual_allocs[0]  # most recent matching annual allocation
 
         # Emergency remaining (sum across all emergency types)
         if not emergency_types:
             continue
         remaining = sum(self._remaining_for(emp, lt) for lt in emergency_types)
         if remaining <= 0:
             continue
 
         # idempotency: skip if this year already added on this allocation
         if self._carry_marker_exists(target_alloc, tomorrow.year):
             continue
 
         # add to existing annual allocation
         target_alloc.sudo().write({
             "number_of_days": (target_alloc.number_of_days or 0.0) + remaining
          })
         target_alloc.message_post(
             body=_("Carryover from Emergency (%s): +%s day(s) applied.") % (tomorrow.year, remaining),
             message_type="comment",
             subtype_xmlid="mail.mt_note",
         )

     return True

