from odoo import fields, models


class POSConfig(models.Model):
    _inherit = 'pos.config'

    manager_user_ids = fields.Many2many('res.users', 'pos_config_manager_user_rel',
                                        'pos_config_id', 'user_id', string='Managers',
                                        domain=lambda self: [('groups_id', '=', self.env.ref('point_of_sale.group_pos_manager').id)])
    iface_validate_close = fields.Boolean(string='Enable Validation for Closing POS',
                                          help=('Enabling this will allow manager to'
                                                ' validate if POS needs to be closed'))
    iface_validate_decrease_quantity = fields.Boolean(string='Enable Validation for Decreasing Quantity',
                                                      help=('Enabling this will allow manager to validate'
                                                            ' the order if need to decrease the quantity'))
    iface_validate_delete_order = fields.Boolean(string='Enable Validation for Order Deletion',
                                                 help=('Enabling this will allow manager to '
                                                       'validate the order if needs to be deleted'))
    iface_validate_delete_orderline = fields.Boolean(string='Enable Validation for Order Line Deletion',
                                                     help=('Enabling this will allow manager to validate'
                                                           ' the order if need to delete an order line'))
    iface_validate_discount = fields.Boolean(string='Enable Validation for Discount',
                                             help=('Enabling this will allow manager to validate'
                                                   ' the order if discount is applicable'))
    iface_validate_payment = fields.Boolean(string='Enable Validation for Payment',
                                            help=('Enabling this will allow manager to '
                                                  'validate the order if needs to be paid'))
    iface_validate_price = fields.Boolean(string='Enable Validation for Price Change',
                                          help=('Enabling this will allow manager to validate '
                                                'the order if changing the price is applicable'))
    iface_validate_cash_move = fields.Boolean(string='Enable Validation for Cash In/Out',
                                              help=('Enabling this will allow manager to '
                                                    'validate if POS needs to cash in/out'))
    iface_validate_Refund = fields.Boolean(string='Enable Validation for Refund',
                                              help=('Enabling this will allow manager to '
                                                    'validate if POS needs to Refund'))
