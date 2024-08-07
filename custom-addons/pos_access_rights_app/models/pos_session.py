# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class PosSessionInherit(models.Model):
	_inherit = "pos.session"

	def pos_active_user_group(self, current_user):
		user = self.env['res.users'].search([('id', '=', current_user['id'])])
		discount = user.has_group('pos_access_rights_app.group_discount_button')
		plus_minus = user.has_group('pos_access_rights_app.group_plus_minus_button')
		payment = user.has_group('pos_access_rights_app.group_payment_button')
		quantity = user.has_group('pos_access_rights_app.group_quantity_button')
		numpad = user.has_group('pos_access_rights_app.group_numpad_button')
		price = user.has_group('pos_access_rights_app.group_price_button')
		partner = user.has_group('pos_access_rights_app.group_customer_button')
		Delete = user.has_group('pos_access_rights_app.group_Delete_button')
		dict_pos_group = {'discount': discount, 'plus_minus': plus_minus, 'payment': payment, 'quantity': quantity,
					'numpad': numpad, 'price': price, 'partner': partner}
		return dict_pos_group
