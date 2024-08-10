from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    manager_user_ids = fields.Many2many(related="pos_config_id.manager_user_ids", readonly=False)
    iface_validate_close = fields.Boolean(related="pos_config_id.iface_validate_close", readonly=False)
    iface_validate_decrease_quantity = fields.Boolean(related="pos_config_id.iface_validate_decrease_quantity", readonly=False)
    iface_validate_delete_order = fields.Boolean(related="pos_config_id.iface_validate_delete_order", readonly=False)
    iface_validate_delete_orderline = fields.Boolean(related="pos_config_id.iface_validate_delete_orderline", readonly=False)
    iface_validate_discount = fields.Boolean(related="pos_config_id.iface_validate_discount", readonly=False)
    iface_validate_payment = fields.Boolean(related="pos_config_id.iface_validate_payment", readonly=False)
    iface_validate_price = fields.Boolean(related="pos_config_id.iface_validate_price", readonly=False)
    iface_validate_cash_move = fields.Boolean(related="pos_config_id.iface_validate_cash_move", readonly=False)
