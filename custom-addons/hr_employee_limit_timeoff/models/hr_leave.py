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

    @api.model
    def create(self, vals):
        self._check_request_date_limit(vals)
        return super().create(vals)

    def write(self, vals):
        self._check_request_date_limit(vals)
        return super().write(vals)

    def _check_request_date_limit(self, vals):
        request_date_from = vals.get('request_date_from') or self.request_date_from
        leave_type_id = vals.get('holiday_status_id') or self.holiday_status_id.id

        if request_date_from and leave_type_id:
            if isinstance(request_date_from, str):
                request_date_from = fields.Date.from_string(request_date_from)

            leave_type = self.env['hr.leave.type'].browse(leave_type_id)
            limit_days = leave_type.leave_request_limit_days

            if limit_days > 0 : 
                max_date = date.today() + timedelta(days=limit_days)
                if request_date_from > max_date:
                    raise ValidationError(_(
                        "You cannot request this leave more than %s days in advance."
                    ) % limit_days)