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
    avg_time_between_customer = fields.Float(string="Avg Time between Customer")
    status = fields.Selection( [
        ('new', 'New'),
    ], string="Status", default='new')

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
                WITH visit_pairs AS (
                    SELECT 
                        curr.id,
                        curr.create_uid,
                        curr.partner_id as current_partner,
                        prev.partner_id as prev_partner,
                        curr.create_date,
                        CASE
                            WHEN DATE(curr.create_date) = DATE(prev.check_out_time)
                            THEN EXTRACT(EPOCH FROM (curr.create_date - prev.check_out_time)) / 60
                            ELSE 0
                        END as time_between_customers
                    FROM daily_visit curr
                    LEFT JOIN LATERAL (
                        SELECT partner_id, check_out_time
                        FROM daily_visit d
                        WHERE d.create_uid = curr.create_uid
                          AND d.create_date < curr.create_date
                        ORDER BY d.create_date DESC
                        LIMIT 1
                    ) prev ON TRUE
                ),
                avg_time_between_pairs AS (
                    SELECT 
                        vp.id,
                        AVG(vp2.time_between_customers) as avg_time_between_customer
                    FROM visit_pairs vp
                    LEFT JOIN visit_pairs vp2 ON (
                        vp2.create_uid = vp.create_uid 
                        AND vp2.prev_partner = vp.prev_partner 
                        AND vp2.current_partner = vp.current_partner
                        AND vp2.create_date < vp.create_date
                        AND vp2.time_between_customers > 0
                        AND vp2.id IN (
                            SELECT vp3.id 
                            FROM visit_pairs vp3
                            WHERE vp3.create_uid = vp.create_uid 
                              AND vp3.prev_partner = vp.prev_partner 
                              AND vp3.current_partner = vp.current_partner
                              AND vp3.create_date < vp.create_date
                              AND vp3.time_between_customers > 0
                            ORDER BY vp3.create_date DESC
                            LIMIT 3
                        )
                    )
                    GROUP BY vp.id
                ),
                main_data AS (
                    SELECT
                        curr.id,
                        curr.reference,
                        curr.create_uid as created_by,
                        curr.partner_id,
                        curr.create_date as creation_date,
                        curr.check_out_time,
                        curr.is_it_sold,
                        CASE 
                            WHEN curr.check_out_time IS NOT NULL 
                            THEN EXTRACT(EPOCH FROM (curr.check_out_time - curr.create_date)) / 60 
                            ELSE 0 
                        END as time_spending_in_customer,
                        COALESCE(vp.time_between_customers, 0) as time_between_customers,
                        COALESCE(avg_tbl.avg_time_spent_per_customer, 0) as avg_time_spent_per_customer,
                        COALESCE(avg_pairs.avg_time_between_customer, 0) as avg_time_between_customer,
                        curr.status
                    FROM daily_visit curr
                    LEFT JOIN visit_pairs vp ON vp.id = curr.id
                    LEFT JOIN avg_time_between_pairs avg_pairs ON avg_pairs.id = curr.id
                    LEFT JOIN LATERAL (
                        SELECT AVG(EXTRACT(EPOCH FROM (d.check_out_time - d.create_date)) / 60) AS avg_time_spent_per_customer
                        FROM (
                            SELECT check_out_time, create_date
                            FROM daily_visit d
                            WHERE d.partner_id = curr.partner_id
                              AND d.check_out_time IS NOT NULL
                              AND d.create_date IS NOT NULL
                              AND d.create_date < curr.create_date
                            ORDER BY d.create_date DESC
                            LIMIT 3
                        ) d
                    ) avg_tbl ON TRUE
                    WHERE curr.check_out_time IS NOT NULL
                )
                SELECT * FROM main_data
                WHERE (
                    (time_spending_in_customer > avg_time_spent_per_customer AND avg_time_spent_per_customer > 0)
                    OR
                    (time_between_customers > avg_time_between_customer AND avg_time_between_customer > 0)
                )
            )
        """ )
