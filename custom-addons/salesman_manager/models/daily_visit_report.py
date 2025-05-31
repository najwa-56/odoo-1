# models/daily_visit_report.py
from odoo import models, fields, tools
from odoo.exceptions import UserError
class DailyVisitReport(models.Model):
    _name = 'daily.visit.report'
    _description = 'Daily Visit Report'
    _auto = False

    reference = fields.Char(string="Reference")
    created_by = fields.Many2one('res.users', string="Created By")
    partner_id = fields.Many2one('res.partner', string="Customer")
    is_it_sold = fields.Boolean(string="Is It Sold?")
    creation_date = fields.Datetime(string="Check In")
    check_out_time = fields.Datetime(string="Check Out")
    time_spending_in_customer = fields.Float(string="Time Spent (mins)")
    time_between_customers = fields.Float(string="Time Between Customers (mins)")
    avg_time_spent_per_customer = fields.Float(string="Avg Time for Customer")
    tag_max_value = fields.Integer(string="Max Tag Value")

    def action_open_specific_visit (self):
        self.ensure_one()
        # Find the actual daily.visit record
        visit = self.env['daily.visit'].search( [('reference', '=', self.reference)], limit=1 )
        if not visit:
            return

        return {
            'type': 'ir.actions.act_window',
            'name': 'Daily Visit',
            'res_model': 'daily.visit',
            'view_mode': 'form',
            'res_id': visit.id,
            'target': 'current',
        }

    def init (self):
        tools.drop_view_if_exists( self._cr, self._table )
        self._cr.execute( """
            CREATE OR REPLACE VIEW daily_visit_report AS (
                SELECT
                    curr.id,
                    curr.reference,
                    curr.create_uid as created_by,
                    curr.partner_id,
                    curr.create_date as creation_date,
                    curr.check_out_time,
                    curr.is_it_sold,
                    EXTRACT(EPOCH FROM (curr.check_out_time - curr.create_date)) / 60 as time_spending_in_customer,
                    CASE
                        WHEN DATE(curr.create_date) = DATE(prev.check_out_time)
                        THEN EXTRACT(EPOCH FROM (curr.create_date - prev.check_out_time)) / 60
                        ELSE 0
                    END as time_between_customers,
                    avg_tbl.avg_time_spent_per_customer,
                    tag_tbl.tag_max_value
                FROM daily_visit curr
                LEFT JOIN LATERAL (
                    SELECT check_out_time
                    FROM daily_visit d
                    WHERE d.create_uid = curr.create_uid
                      AND d.create_date < curr.create_date
                    ORDER BY d.create_date DESC
                    LIMIT 1
                ) prev ON TRUE
                LEFT JOIN LATERAL (
                    SELECT AVG(EXTRACT(EPOCH FROM (d.check_out_time - d.create_date)) / 60) AS avg_time_spent_per_customer
                    FROM daily_visit d
                    WHERE d.partner_id = curr.partner_id
                      AND d.check_out_time IS NOT NULL
                      AND d.create_date IS NOT NULL
                ) avg_tbl ON TRUE
                LEFT JOIN LATERAL (
                    SELECT MAX(rc.value) AS tag_max_value
                    FROM res_partner_res_partner_category_rel rel
                    JOIN res_partner_category rc ON rc.id = rel.category_id
                    WHERE rel.partner_id = curr.partner_id
                ) tag_tbl ON TRUE
            )
        """ )
