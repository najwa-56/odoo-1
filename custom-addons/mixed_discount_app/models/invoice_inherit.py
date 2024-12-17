# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import re

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	multi_discount = fields.Char(string="Mixed Discount(%)")

	@staticmethod
	def sale_discount(discount):
		rep = re.compile(
			r'^(\s*[-+]{0,1}\s*\d+([,.]\d+)?){1}'
			r'(\s*[-+]\s*\d+([,.]\d+)?\s*)*$'
		)
		if discount and not rep.match(discount):
			return False
		return True

	@api.onchange('multi_discount')
	def get_multi_discount(self):
		def get_discount(discount):
			discount = discount.replace(" ", "")
			discount = discount.replace(",", ".")
			if discount and discount[0] == '+':
				discount = discount[1:]
			return discount

		for sale_id in self:
			if sale_id.multi_discount:
				if self.sale_discount(sale_id.multi_discount):
					new_discount = get_discount(
						sale_id.multi_discount)
				else:
					sale_id.discount = 0
					raise UserError(
						_('Please enter correct discount.'))

				split_reg = re.split(r'([+-])', new_discount)
				discount_list = []
				x = 1
				for logit in split_reg:
					if logit == '-':
						x = -1
					elif logit == '+':
						x = 1
					else:
						discount_list.append(float(logit) * x)
				rep_discount = 1
				for logit in discount_list:
					rep_discount = rep_discount * (1 - (logit / 100))
				total_dis = 1 - rep_discount
				sale_id.discount = total_dis * 100

				if new_discount != sale_id.multi_discount:
					sale_id.multi_discount = new_discount

			else:
				sale_id.discount = 0

	@api.constrains('multi_discount')
	def check_discount(self):
		for sale_id in self:
			if sale_id.multi_discount and not self.sale_discount(
					sale_id.multi_discount):
				raise ValidationError(
					_('Please enter correct discount.'))

	def write(self, vals):
		res = super(AccountMoveLine, self).write(vals)
		if 'multi_discount' in vals:
			for sale_id in self:
				sale_id.get_multi_discount()
		return res


class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'

	def _prepare_account_move_line(self, move=False):
		move_line_vals = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
		if 'purchase_line_id' in  move_line_vals:
			po_line = move_line_vals.get('purchase_line_id')
			po_line_id = self.env['purchase.order.line'].browse(po_line)
			move_line_vals.update({'discount':po_line_id.discount, 'multi_discount':po_line_id.multi_discount})
		return move_line_vals