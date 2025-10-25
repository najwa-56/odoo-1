# your_module/models/hr_leave_allocation.py
from odoo import models, fields


FIVE = (16, 5)

class HrLeave(models.Model):
    _inherit = "hr.leave"
    # مدة الإجازة في الطلب
    number_of_days = fields.Float(digits=FIVE)
    number_of_days_display = fields.Float(digits=FIVE)
    # لو عندك عرض بالساعات
    number_of_hours_display = fields.Float(digits=FIVE)

    
class HrLeaveAllocation(models.Model):
    _inherit = "hr.leave.allocation"
    # مدة الإعتماد/التخصيص
    number_of_days = fields.Float(digits=FIVE)
    number_of_days_display = fields.Float(digits=FIVE)