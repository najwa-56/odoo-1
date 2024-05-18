# -- coding: utf-8 --
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.


from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    words_amount = fields.Char(string='In Words', compute='_compute_amount_total_words')

    @api.depends('amount', 'currency_id')
    def _compute_amount_total_words(self):
        self.words_amount = self.currency_id.amount_to_text(self.amount)
        return self.words_amount
