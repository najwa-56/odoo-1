# -*- coding: utf-8 -*-
###############################################################################
#    Cybrosys Technologies Pvt. Ltd.  (modified for yearly periodized usage)
###############################################################################
from odoo import fields, models, tools

APPROVED_LEAVE_STATES = ("validate", "validate1")


class ReportBalanceLeave(models.Model):
    """Balance Leave Report model (with allocation-based yearly periods)"""

    _name = 'report.balance.leave'
    _description = 'Leave Balance Report'
    _auto = False

    # ----- -----
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
                                    readonly=True, help="Leave type of employee")
    allocated_days = fields.Float(string='Allocated Balance',
                                  help="Total leave assigned to the employee")
    taken_days = fields.Float(string='Taken Leaves',
                              help="Taken leaves of employee")
    balance_days = fields.Float(string='Remaining Balance',
                                help="Remaining leaves of employee")
    company_id = fields.Many2one('res.company', string="Company",
                                 help="Company Name")

    # ----- -----
    allocation_id = fields.Many2one('hr.leave.allocation', string='Allocation', readonly=True)
    period_index = fields.Integer(string='Period #', readonly=True)
    period_label = fields.Char(string='Period', readonly=True)          # مثال: 2022-2023
    period_start = fields.Date(string='Period Start', readonly=True)
    period_end = fields.Date(string='Period End', readonly=True)
    taken_in_period = fields.Float(string='Taken in Period', readonly=True)
    allocated_in_period = fields.Float(
    string='Allocated in Period',
    help="Annual allocation for this period based on seniority and leave kind"
             )
    balance_in_period = fields.Float(
    string='Balance in Period',
    help="Remaining balance in this period"
    )

    carried_balance = fields.Float(
    string='Carried Balance',
    help="Allocated in current period + limited carryover from previous period (min 1, max 7)"
)



    def init(self):
        """Create/refresh SQL view"""
        tools.drop_view_if_exists(self._cr, 'report_balance_leave')
        self._cr.execute("""
            CREATE OR REPLACE VIEW report_balance_leave AS
            WITH emp AS (
                SELECT e.id AS emp_id, e.gender, e.country_id, e.department_id,
                       e.job_id, e.company_id
                FROM hr_employee e
                WHERE e.active = TRUE
            ),
            alloc AS (
                /* all allocations */
                SELECT
                    a.id AS allocation_id,
                    a.employee_id AS emp_id,
                    a.holiday_status_id AS leave_type_id,
                    COALESCE(a.date_from::date, a.create_date::date) AS alloc_start,
                    a.number_of_days
                FROM hr_leave_allocation a
                WHERE a.state IN %(APPROVED)s
            ),
            totals_alloc AS (
                /* total alloction for each employee*/
                SELECT emp_id, leave_type_id, SUM(number_of_days)::float AS allocated_total
                FROM alloc
                GROUP BY emp_id, leave_type_id
            ),
            totals_taken AS (
                /* total taken for each employee/leave type */
                SELECT l.employee_id AS emp_id, l.holiday_status_id AS leave_type_id,
                       SUM(l.number_of_days)::float AS taken_total
                FROM hr_leave l
                WHERE l.state IN %(APPROVED)s
                GROUP BY l.employee_id, l.holiday_status_id
            ),
            periodized AS (
    SELECT
        alloc.allocation_id,
        alloc.emp_id,
        alloc.leave_type_id,
        gs.idx AS period_index,
        (alloc.alloc_start + (gs.idx || ' year')::interval)::date AS period_start,
        ((alloc.alloc_start + ((gs.idx + 1) || ' year')::interval)::date - 1) AS period_end
    FROM alloc
    JOIN LATERAL (
        SELECT generate_series(
            0,
            (
              GREATEST(
                0,
                FLOOR( ((now()::date - alloc.alloc_start)::int)::numeric / 365.25 )
              )::int
            )
        ) AS idx
    ) gs ON TRUE
),

            leaves AS (
                SELECT
                    l.id,
                    l.employee_id AS emp_id,
                    l.holiday_status_id AS leave_type_id,
                    l.date_from::date AS lf,
                    l.date_to::date   AS lt,
                    NULLIF((l.date_to::date - l.date_from::date + 1),0) AS span_days,
                    l.number_of_days AS ndays
                FROM hr_leave l
                WHERE l.state IN %(APPROVED)s
            ),
            joined AS (
                /* link each allocation period with matching leaves and calculate overlap */
                SELECT
                    p.allocation_id,
                    p.emp_id,
                    p.leave_type_id,
                    p.period_index,
                    p.period_start,
                    p.period_end,
                    CASE
                        WHEN leaves.span_days IS NULL OR leaves.span_days = 0 THEN 0
                        ELSE leaves.ndays * GREATEST(
                                0,
                                (LEAST(p.period_end, leaves.lt)
                                 - GREATEST(p.period_start, leaves.lf) + 1)
                            )::float / leaves.span_days::float
                    END AS ndays_in_period
                FROM periodized p
                LEFT JOIN leaves
                  ON leaves.emp_id = p.emp_id
                 AND leaves.leave_type_id = p.leave_type_id
                 AND daterange(p.period_start, p.period_end + 1, '[]')
                     && daterange(leaves.lf, leaves.lt + 1, '[]')
            ),
            per_period AS (
                /* total taken within each allocation year */
                SELECT
                    j.allocation_id,
                    j.emp_id,
                    j.leave_type_id,
                    j.period_index,
                    j.period_start,
                    j.period_end,
                    COALESCE(SUM(j.ndays_in_period),0.0) AS taken_in_period
                FROM joined j
                GROUP BY j.allocation_id, j.emp_id, j.leave_type_id,
                         j.period_index, j.period_start, j.period_end
            )
            SELECT
                /* id */
                row_number() over () AS id,

                e.emp_id AS emp_id,
                e.gender AS gender,
                e.country_id AS country_id,
                e.department_id AS department_id,
                e.job_id AS job_id,
                p.leave_type_id AS leave_type_id,
                /* الإجماليات الأصلية */
                COALESCE(ta.allocated_total, 0.0) AS allocated_days,
                COALESCE(tt.taken_total, 0.0)     AS taken_days,
                COALESCE(ta.allocated_total, 0.0) - COALESCE(tt.taken_total, 0.0) AS balance_days,
                e.company_id AS company_id,
                CASE
    WHEN lt.leave_kind = 'annual' THEN
        CASE
            WHEN EXTRACT(YEAR FROM age(p.period_start, a.alloc_start)) < 5
                THEN 16.0
            ELSE 20.0
        END
    WHEN lt.leave_kind = 'emergency' THEN 5.0
    ELSE 0.0
END AS allocated_in_period,

CASE
    WHEN lt.leave_kind = 'annual' THEN
        CASE
            WHEN EXTRACT(YEAR FROM age(p.period_start, a.alloc_start)) < 5
                THEN 16.0
            ELSE 20.0
        END - p.taken_in_period
    WHEN lt.leave_kind = 'emergency' THEN 5.0 - p.taken_in_period
    ELSE 0.0
END AS balance_in_period,
                         
                         LEAST(
    7,
    GREATEST(
        0,
        LAG(
            CASE
                WHEN lt.leave_kind = 'annual' THEN
                    CASE
                        WHEN EXTRACT(YEAR FROM age(p.period_start, a.alloc_start)) < 5
                            THEN 16.0
                        ELSE 20.0
                    END - p.taken_in_period
                WHEN lt.leave_kind = 'emergency' THEN 5.0 - p.taken_in_period
                ELSE 0.0
            END
        ) OVER (PARTITION BY p.emp_id, p.leave_type_id ORDER BY p.period_index)
    )
) + 
CASE
    WHEN lt.leave_kind = 'annual' THEN
        CASE
            WHEN EXTRACT(YEAR FROM age(p.period_start, a.alloc_start)) < 5
                THEN 16.0
            ELSE 20.0
        END
    WHEN lt.leave_kind = 'emergency' THEN 5.0
    ELSE 0.0
END AS carried_balance,




                /* new fields for periods */
                p.allocation_id AS allocation_id,
                p.period_index  AS period_index,
                to_char(p.period_start,'YYYY') || '-' || to_char(p.period_end,'YYYY') AS period_label,
                p.period_start  AS period_start,
                p.period_end    AS period_end,
                p.taken_in_period AS taken_in_period

            FROM per_period p
            JOIN emp e
              ON e.emp_id = p.emp_id
            LEFT JOIN totals_alloc ta
              ON ta.emp_id = p.emp_id AND ta.leave_type_id = p.leave_type_id
            LEFT JOIN totals_taken tt
              ON tt.emp_id = p.emp_id AND tt.leave_type_id = p.leave_type_id
            JOIN hr_leave_type lt
              ON lt.id = p.leave_type_id
            JOIN alloc a
              ON a.allocation_id = p.allocation_id

            ORDER BY e.emp_id, p.leave_type_id, p.period_start;
            

                         
                         
        """, {'APPROVED': APPROVED_LEAVE_STATES})
        

