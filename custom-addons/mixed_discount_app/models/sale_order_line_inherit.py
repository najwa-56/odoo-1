# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import re


class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'

	multi_discount = fields.Char(string="Mixed Discount(%)")

	def _prepare_invoice_line(self, sequence):
		invoice_line_vals = super(SaleOrderLine, self)._prepare_invoice_line(sequence=sequence)
		invoice_line_vals.update({'multi_discount':self.multi_discount})
		return invoice_line_vals

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
		res = super(SaleOrderLine, self).write(vals)
		if 'multi_discount' in vals:
			for sale_id in self:
				sale_id.get_multi_discount()
		return res