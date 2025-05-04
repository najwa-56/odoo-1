from odoo import models, fields, api


class RouteLine(models.Model):
    _inherit = 'route.line'

    #for changing the string name
    cust_tree_ids = fields.One2many(string='العملاء')

class Chatterr(models.Model):
    _name = 'route.line'
    _inherit = ['route.line', 'mail.thread', 'mail.activity.mixin']
