from odoo import models, fields, api

class TaskTag(models.Model):
    _name = 'task.tag'
    _description = 'Task Tag'

    name = fields.Char(string='Tag Name', required=True)
    color = fields.Integer(string='Color')

