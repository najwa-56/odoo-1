from odoo import models, fields, api
from datetime import datetime,date


class WeeklyRoutsLine(models.Model):
    _name = 'weekly.routs.line'
    _description = 'Weekly Routes Line'


    weekly_route_id = fields.Many2one('weekly.routs', string="المسار الأسبوعي", ondelete='cascade')
    day = fields.Date(string="اليوم")
    delivery_route_id = fields.Many2one('delivery.route', string="المنطقة") # there is many values of "المنطقة" and we want to select only one value
    delivery_line_ids = fields.Many2many('route.line' ,string="المسارات")   # there is many values of "المسارات" and we want to select many  values and we need to use wedget many2man7

    # this field to show day name in Arabic
    day_name = fields.Char(string="اسم اليوم", compute="_compute_day_name", store=True)
    @api.depends('day')
    def _compute_day_name(self):
        """Compute the day of the week in Arabic"""
        # Arabic days map
        arabic_days = {
            0: 'الاثنين',  # Monday
            1: 'الثلاثاء',  # Tuesday
            2: 'الأربعاء',  # Wednesday
            3: 'الخميس',  # Thursday
            4: 'الجمعة',  # Friday
            5: 'السبت',  # Saturday
            6: 'الأحد'  # Sunday
        }

        for record in self:
            if record.day:
                try:
                    # Get the day of the week (0 for Monday to 6 for Sunday)
                    day_of_week = datetime.strptime(str(record.day), '%Y-%m-%d').weekday()
                    record.day_name = arabic_days[day_of_week]
                except Exception:
                    record.day_name = ''
            else:
                record.day_name = ''



