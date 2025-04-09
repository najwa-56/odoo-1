# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp
import re





class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    global_discount = fields.Float(string="Global Discount",digits='Discount')
    per_product_discount = fields.Float(string="Per Product Discount", compute="_compute_per_product_discount", digits='Discount' , store=True)

    @api.depends('global_discount')
    def _compute_per_product_discount(self):
        for order in self:
            order.per_product_discount = order.global_discount / order.amount_total if order.amount_total > 0 else 1 

    def action_apply_global_discount(self):
        for order in self:
            for line in order.order_line:
                if line.price_unit == 0:
                    continue
                line.discount =  order.per_product_discount
				


class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'

	multi_discount = fields.Char(string="Mixed Discount(%)")
	discount = fields.Float(string='Discount(%)', digits=dp.get_precision('Discount'), default=0.0)

	fix_discount = fields.Float(string='Static Discount', digits=dp.get_precision('Discount'), default=0.0)


	@staticmethod
	def purchase_discount(discount):
		rep = re.compile(
			r'^(\s*[-+]{0,1}\s*\d+([,.]\d+)?){1}'
			r'(\s*[-+]\s*\d+([,.]\d+)?\s*)*$'
		)
		if discount and not rep.match(discount):
			return False
		return True
	
	@api.onchange("fix_discount")
	def get_fix_discount(self):
		for line in self:
			self.get_multi_discount()
			if line.fix_discount > 0:
				# Calculate the line's total price before discount
				total_price = line.price_unit * line.product_qty
				# Avoid division by zero
				if total_price > 0:
					# Calculate the fixed discount as a percentage of the total price
					fix_discount_percentage = (line.fix_discount / total_price) * 100.0

					# Update the discount percentage
					line.discount += fix_discount_percentage
				

			line._compute_amount()

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
				if self.purchase_discount(sale_id.multi_discount):
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
			if sale_id.multi_discount and not self.purchase_discount(
					sale_id.multi_discount):
				raise ValidationError(
					_('Please enter correct discount.'))

	def write(self, vals):
		res = super(PurchaseOrderLine, self).write(vals)
		if 'multi_discount' in vals:
			for sale_id in self:
				sale_id.get_multi_discount()
		return res


	# @api.depends('product_qty', 'product_uom', 'company_id', 'purchase_multi_uom_cost')
    # def _compute_price_unit_and_date_planned_and_name(self):
	# 	super()._compute_price_unit_and_date_planned_and_name()
    #     for line in self:
	# 		line.price_unit = float_round(line.product_id.standard_price, precision_digits=max(line.currency_id.decimal_places,
    #                                                                    self.env['decimal.precision'].precision_get(
    #                                                                        'Product Price')))

	# @api.depends('discount')
	# def _compute_amount(self):
	# 	for sale_id in self:
	# 		price_unit = False
	# 		price = sale_id.recalculate_amount()
	# 		if price != sale_id.price_unit:
	# 			price_unit = sale_id.price_unit
	# 			sale_id.price_unit = price
	# 		super(PurchaseOrderLine, sale_id)._compute_amount()
	# 		if price_unit:
	# 			sale_id.price_unit = price_unit

	# def recalculate_amount(self):
	# 	self.ensure_one()
	# 	if self.discount:
	# 		return self.price_unit * (1 - self.discount / 100)
	# 	return self.price_unit	

	# def _get_stock_move_price_unit(self):
	# 	price_unit = False
	# 	price = self.recalculate_amount()
	# 	if price != self.price_unit:
	# 		price_unit = self.price_unit
	# 		self.price_unit = price
	# 	price = super(PurchaseOrderLine, self)._get_stock_move_price_unit()
	# 	if price_unit:
	# 		self.price_unit = price_unit
	# 	return price