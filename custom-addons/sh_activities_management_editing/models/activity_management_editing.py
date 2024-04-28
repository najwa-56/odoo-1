from odoo import models, fields

class ActivityEditing(models.Model):
    _inherit = 'mail.activity'



    #chainging the name of these fields
    user_id = fields.Many2one(string='مسندة لـ')
    activity_type_id = fields.Many2one(string='إسم المهمة')
    summary = fields.Char(string='الملخص')
    date_deadline = fields.Date(string='تاريخ الانتهاء')
    feedback = fields.Text(string='ردود الفعل')