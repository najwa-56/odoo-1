from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta, date

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    leave_request_limit_days = fields.Integer(
        string="Max Days to Request in Advance",
        default=30,
        help="Maximum number of days in advance that this leave type can be requested."
    )

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    @api.constrains('request_date_from', 'holiday_status_id')
    def _check_request_date_limit(self):
        for leave in self:
            if leave.request_date_from and leave.holiday_status_id:
                limit_days = leave.holiday_status_id.leave_request_limit_days
                if limit_days > 0:
                    max_date = date.today() + timedelta(days=limit_days)
                    if leave.request_date_from > max_date:
                        raise ValidationError(_(
                            "You cannot request this leave more than %s days in advance."
                        ) % limit_days)
