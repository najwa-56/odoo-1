from odoo import models, fields, tools

class DailyRealtimeReport(models.Model):
    _name = 'daily.realtime.report'
    _description = 'Real-time Daily Visit Report'
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
    tag_max_value = fields.Float(string="Max Tag Value")
    status = fields.Selection( [
        ('new', 'New'),
    ], string="Status" )

    def action_open_specific_visit (self):
        self.ensure_one()
        visit = self.env['daily.visit'].search( [('reference', '=', self.reference)], limit=1 )
        if visit:
            if visit.status == 'new':
                visit.status = ''
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
            CREATE OR REPLACE VIEW daily_realtime_report AS (
                SELECT * FROM (
                    SELECT
                        curr.id,
                        curr.reference,
                        curr.create_uid AS created_by,
                        curr.partner_id,
                        curr.create_date AS creation_date,
                        curr.check_out_time,
                        curr.is_it_sold,
                        curr.status,
                        EXTRACT(EPOCH FROM (curr.check_out_time - curr.create_date)) / 60 AS time_spending_in_customer,
                        CASE
                            WHEN prev.check_out_time IS NOT NULL
                                 AND DATE(curr.create_date) = DATE(prev.check_out_time)
                            THEN EXTRACT(EPOCH FROM (curr.create_date - prev.check_out_time)) / 60
                            ELSE 0
                        END AS time_between_customers,
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
                        SELECT MAX(CAST(rc.value AS FLOAT)) AS tag_max_value
                        FROM res_partner_res_partner_category_rel rel
                        JOIN res_partner_category rc ON rc.id = rel.category_id
                        WHERE rel.partner_id = curr.partner_id
                    ) tag_tbl ON TRUE
                ) AS subquery
                WHERE 
                    time_spending_in_customer > COALESCE(avg_time_spent_per_customer, 0)
                    OR time_between_customers > COALESCE(tag_max_value, 0)
            )
        """ )
