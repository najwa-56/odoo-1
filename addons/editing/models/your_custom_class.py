from odoo import fields,models, api

class StockPickingCustom(models.Model):
    _inherit = 'stock.picking'
    def button_validate(self):
        super(StockPickingCustom, self).button_validate()

