# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models, tools
from datetime import datetime, timedelta
import logging


class ReportBalanceLeave(models.Model):
    """Balance Leave Report model"""

    _name = 'report.balance.leave'
    _description = 'Leave Balance Report'
    _auto = False

    emp_id = fields.Many2one('hr.employee', string="Employee", readonly=True,
                             help="Employee name")
    gender = fields.Char(string='gender', readonly=True,
                         help="Employee Gender")
    department_id = fields.Many2one('hr.department', string='Department',
                                    readonly=True, help="Department Name")
    country_id = fields.Many2one('res.country', string='Nationality',
                                 readonly=True, help="Country Name")
    job_id = fields.Many2one('hr.job', string='Job', readonly=True,
                             help="Job of employee")
    leave_type_id = fields.Many2one('hr.leave.type', string='Leave Type',
                                    readonly=True, help="Leave type of "
                                                        "employee")
    allocated_days = fields.Integer(string='Allocated Balance',
                                    help="Total leave assigned to "
                                         "the employee")
    taken_days = fields.Integer(string='Taken Leaves', help="Taken leaves of "
                                                            "employee")
    balance_days = fields.Integer(string='Remaining Balance',
                                  help="Remaining leaves of employee")
    company_id = fields.Many2one('res.company', string="Company",
                                 help="Company Name")
    allocation_id = fields.Many2one(
        'hr.leave.allocation',
        string="Allocation",
        readonly=True,
        help="Source allocation record"
    )
    allocation_date_from = fields.Date(
        string="Allocation Start",
        readonly=True
    )
    allocation_date_to = fields.Date(
        string="Allocation End",
        readonly=True
    )

    def init(self):
        """Loads report data (period-aware per allocation)."""
        tools.drop_view_if_exists(self._cr, 'report_balance_leave')
        self._cr.execute("""
            CREATE OR REPLACE VIEW report_balance_leave AS (
                SELECT
                    row_number() OVER (ORDER BY e.id, lt.id, al.id) AS id,
                    e.id                                AS emp_id,
                    e.gender                            AS gender,
                    e.country_id                        AS country_id,
                    e.department_id                     AS department_id,
                    e.job_id                            AS job_id,
                    lt.id                               AS leave_type_id,

                    -- Allocation total (this allocation only)
                    COALESCE(al.number_of_days, 0)      AS allocated_days,

                    -- Taken days that overlap the allocation's period
                    COALESCE(
                        SUM(
                            CASE
                                WHEN l.id IS NOT NULL
                                     AND l.state = 'validate'
                                     AND l.holiday_status_id = lt.id
                                     AND l.employee_id = e.id
                                     -- overlap condition between [l.request_date_from, l.request_date_to]
                                     -- and [al.date_from, al.date_to or open end]
                                     AND l.request_date_from <= COALESCE(al.date_to, DATE '9999-12-31')
                                     AND l.request_date_to   >= COALESCE(al.date_from, DATE '0001-01-01')
                                THEN l.number_of_days
                                ELSE 0
                            END
                        ), 0
                    )                                   AS taken_days,

                    -- Remaining = allocation - taken inside its period
                    COALESCE(al.number_of_days, 0)
                    - COALESCE(
                        SUM(
                            CASE
                                WHEN l.id IS NOT NULL
                                     AND l.state = 'validate'
                                     AND l.holiday_status_id = lt.id
                                     AND l.employee_id = e.id
                                     AND l.request_date_from <= COALESCE(al.date_to, DATE '9999-12-31')
                                     AND l.request_date_to   >= COALESCE(al.date_from, DATE '0001-01-01')
                                THEN l.number_of_days
                                ELSE 0
                            END
                        ), 0
                      )                                 AS balance_days,

                    e.company_id                        AS company_id,

                    -- Expose allocation window to filter/report by period
                    al.date_from                        AS allocation_date_from,
                    al.date_to                          AS allocation_date_to,
                    al.id                               AS allocation_id

                FROM hr_employee e
                JOIN hr_leave_allocation al
                    ON al.employee_id = e.id
                   AND al.state = 'validate'
                JOIN hr_leave_type lt
                    ON lt.id = al.holiday_status_id
                LEFT JOIN hr_leave l
                    ON l.employee_id = e.id
                   AND l.holiday_status_id = lt.id
                   AND l.state = 'validate'
                WHERE e.active = TRUE
                GROUP BY
                    e.id, e.gender, e.country_id, e.department_id, e.job_id,
                    lt.id,
                    al.id, al.date_from, al.date_to,
                    e.company_id
            )
        """)

    def create_annual_allocation_for_emergency_leaves(self):
        """Create annual leave allocation for employees whose emergency leave ends tomorrow."""
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        emergency_leaves = self.search([
            ('leave_type_id.is_emergency', '=', 'yes'),
            ('allocation_date_to', '=', tomorrow)
        ])
        _logger.info("Found %s emergency leave records ending tomorrow.", len(emergency_leaves))
        annual_leave_type = self.env['hr.leave.type'].search([('is_annual', '=', 'yes')], limit=1)
        for record in emergency_leaves:
            if annual_leave_type:
                _logger.info("Creating allocation for employee %s", record.emp_id.name)
                self.env['hr.leave.allocation'].create({
                    'employee_id': record.emp_id.id,
                    'holiday_status_id': annual_leave_type.id,
                    'number_of_days': record.balance_days,
                    'state': 'confirm',  # Use 'confirm' for new allocations
                    'allocation_type': 'regular',
                    'date_from': tomorrow,
                    'date_to': tomorrow + timedelta(days=365),
                })






