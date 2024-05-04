# -*- coding: utf-8 -*-

from odoo import api, fields, models


class pos_config(models.Model):
    _inherit = 'pos.config'

    allow_default_cash = fields.Boolean(string='Set Default Cash Opening')
    default_opening = fields.Float(string='Editable Opening Amount')
    hide_closing = fields.Boolean(string='Hide Closing Summary')


class PosSession(models.Model):
    _inherit = 'pos.session'

    def action_pos_session_open(self):
        # we only open sessions that haven't already been opened
        for session in self.filtered(lambda session: session.state == 'opening_control'):
            values = {}
            if not session.start_at:
                values['start_at'] = fields.Datetime.now()
            if session.config_id.cash_control and not session.rescue:
                last_session = self.search(
                    [('config_id', '=', session.config_id.id), ('id', '!=', session.id)], limit=1)
                # defaults to 0 if lastsession is empty
                session.cash_register_balance_start = last_session.cash_register_balance_end_real
                if self.config_id.allow_default_cash:
                    session.cash_register_balance_start = self.config_id.default_opening
            else:
                values['state'] = 'opened'
            session.write(values)
        return True

    def get_closing_control_data(self):
        closing_control_data = super().get_closing_control_data()
        
        if self.config_id.allow_default_cash:
            orders = self.order_ids.filtered(
                lambda o: o.state == 'paid' or o.state == 'invoiced')
            payments = orders.payment_ids.filtered(
                lambda p: p.payment_method_id.type != "pay_later")
            cash_payment_method_ids = self.payment_method_ids.filtered(
                lambda pm: pm.type == 'cash')
            default_cash_payment_method_id = cash_payment_method_ids[
                0] if cash_payment_method_ids else None
            total_default_cash_payment_amount = sum(payments.filtered(
                lambda p: p.payment_method_id == default_cash_payment_method_id).mapped('amount')) if default_cash_payment_method_id else 0

            closing_control_data['default_cash_details']['amount'] = self.config_id.default_opening + \
                total_default_cash_payment_amount + \
                sum(self.sudo().statement_line_ids.mapped('amount'))
            closing_control_data['default_cash_details']['opening'] = self.config_id.default_opening
        return closing_control_data


    @api.depends('payment_method_ids', 'order_ids', 'cash_register_balance_start')
    def _compute_cash_balance(self):
        for session in self:
            cash_payment_method = session.payment_method_ids.filtered('is_cash_count')[:1]
            if cash_payment_method:
                total_cash_payment = 0.0
                last_session = session.search([('config_id', '=', session.config_id.id), ('id', '<', session.id)], limit=1)
                result = self.env['pos.payment']._read_group([('session_id', '=', session.id), ('payment_method_id', '=', cash_payment_method.id)], aggregates=['amount:sum'])
                total_cash_payment = result[0][0] or 0.0
                if session.state == 'closed':
                    session.cash_register_total_entry_encoding = session.cash_real_transaction + total_cash_payment
                else:
                    session.cash_register_total_entry_encoding = sum(session.statement_line_ids.mapped('amount')) + total_cash_payment
                
                closing_buffer_val = self.config_id.default_opening if self.config_id.allow_default_cash else last_session.cash_register_balance_end_real
                session.cash_register_balance_end = closing_buffer_val + session.cash_register_total_entry_encoding
                session.cash_register_difference = session.cash_register_balance_end_real - session.cash_register_balance_end
            else:
                session.cash_register_total_entry_encoding = 0.0
                session.cash_register_balance_end = 0.0
                session.cash_register_difference = 0.0
