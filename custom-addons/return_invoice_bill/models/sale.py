from odoo import api, fields, models


class SaleOrder(models.Model):
    """This class extends the 'stock.picking' model to add a method for
    retrieving credit notes and debit notes related
    to the picking, and generating actions for viewing them."""
    _inherit = 'sale.order.line'

    def _get_outgoing_incoming_moves(self):
        res = super()._get_outgoing_incoming_moves()
        return res
    