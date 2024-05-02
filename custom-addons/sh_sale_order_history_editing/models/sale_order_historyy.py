
from odoo import models, fields, api

class SaleOrderHistory(models.Model):
    _inherit = 'sale.order.history'
    # adding customer
    partner_id = fields.Many2one(
        "res.partner",
        related="name.order_id.partner_id", store=True
    )

    # adding customer

    # adding الجرد
    product_uom_qtyy = fields.Float(
        "الجرد",
        related="name.aljard",
        store=True
    )

    #alsarf
    alsarf = fields.Float("الصرف", compute="_compute_alsarf",store=True)
    @api.depends("product_uom_qty", "product_uom_qtyy", "alsarf", "order_id.partner_id")
    def _compute_alsarf(self):
        for record in self:

            previous_record = self.search([('id', '<', record.id),
                                           ('partner_id', '=', record.partner_id.id),
                                           ('product_id', '=', record.product_id.id)],
                                          limit=1, order='id desc')
            if previous_record:
              record.alsarf = (previous_record.product_uom_qty + previous_record.product_uom_qtyy) - record.product_uom_qtyy
            else:
                record.alsarf = 0




class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    aljard = fields.Float('الجرد', store=True)

    #NOW LIN ORDER_ID IN SALE HISTOR "NAME" TO SALE ORDER LINE
    order_history_line = fields.One2many( 'sale.order.history', 'name', string='Order History Lines')
    #----------------------------------------------

    #then link alserf field to alsarf in sale order history by order id "order_history_line"
    alsarf = fields.Float('الصرف', related='order_history_line.alsarf',store=True, readonly=True)
    #---------------------------------------------
    #value from multiplied alsarf .
    multiplied_field = fields.Float('Multiplied Field', compute='_compute_multiplied_field', store=True, readonly=True)
    #-----------------------------------
    #this method to show vlue and updat the record for field alsarf in sales order line whenever user add new vallue in aljard field .
    @api.onchange('aljard')
    def _onchange_aljard(self):
        if self.order_id:
            previous_record = self.env['sale.order.history'].search([
                ('order_id', '=', self.order_id.id),
                ('product_id', '=', self.product_id.id)],
                limit=1, order='id desc')
            alsarf_value = (previous_record.product_uom_qty + previous_record.product_uom_qtyy) - self.aljard

            if previous_record:
                self.alsarf = alsarf_value

            else:
                self.alsarf = 0.0





    #-----------------------------------------------------
    #multiplied alsarf * price

    @api.depends('alsarf', 'order_history_line.price_unit')
    def _compute_multiplied_field(self):
        for record in self:
            # Check if there are multiple order history lines for the current record
            if len(record.order_history_line) > 1:
                # Perform a specific calculation when multiple order history lines are present
                # Modify this part based on your business logic
                multiplied_values = [line.alsarf * line.price_unit for line in record.order_history_line]
                record.multiplied_field = sum(multiplied_values)
            else:
                # Perform a calculation for a single order history line
                record.multiplied_field = record.alsarf * record.order_history_line.price_unit
     #_______________________________________________________________
     #The create and write methods in the SaleOrderLine model are modified to trigger the computation of the total in the sale.order model
     # whenever a new record is created or an existing record is modified.
    @api.model
    def create(self, values):
        # Call the parent create method
        record = super(SaleOrderLine, self).create(values)

        # Call the method to update the total in sale order
        if record.order_id:
            record.order_id._compute_total_multiplied_field()

        return record
    def write(self, values):
        # Call the parent write method
        result = super(SaleOrderLine, self).write(values)

        # Call the method to update the total in sale order
        if self.order_id:
           self.order_id._compute_total_multiplied_field()

        return result


class AccountMove(models.Model):
    _inherit = "account.move"

    # this field to link account move with sale order
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        help='Link to the corresponding sale order.',
    )
    # We creat new field name total_multiplied_field_sale_order to add value that in sale order inside it ..

    total_multiplied_field_sale_order = fields.Float(
        string='المجموع المستحق لهذه الفاتوره ',
        store=True,readonly=True  )

    # ovirraide the function that is in account move and add eidt
    # it that make the value in total_multiplied_field in sale order visible in new field in account move total_multiplied_field_sale_order.

    def action_post(self):
        result = super(AccountMove, self).action_post()

        # If sale_order_id is not set, try to find it based on the invoice lines
        if not self.sale_order_id and self.invoice_line_ids:
            sale_order_lines = self.invoice_line_ids.mapped('sale_line_ids')
            sale_orders = sale_order_lines.mapped('order_id')

            # If there is only one sale order linked to the invoice lines, set it as sale_order_id
            if len(sale_orders) == 1:
                self.sale_order_id = sale_orders

        # Retrieve the Sale Order linked to the Account Move
        sale_order = self.sale_order_id

        if sale_order:
            # Assign the value of total_multiplied_field from Sale Order to Account Move
            self.total_multiplied_field_sale_order = sale_order.total_multiplied_field

        return result



    #--------------------------------------------------
    # the way to show to balance of each invoice
    # --------------------------------------------------

    total_balance = fields.Float(
        string='Total Balance',
        compute='_compute_total_balance',
        store=True,
        readonly=True,
        help='Sum of total_multiplied_field_sale_order for all invoices.'
    )

    sum_total_balance = fields.Float(
        string=' sum Total Balance',
        compute='_compute_sum_total_balance',
        store=True,
        readonly=True,
        help='Sum of total_balance for all records.'
    )

     # to find total_multiplied_field_sale_order for each invoice
    @api.depends('total_multiplied_field_sale_order')
    def _compute_total_balance(self):
        for move in self:
            total_balance = sum(move.mapped('total_multiplied_field_sale_order'))
            move.total_balance = total_balance

    @api.depends('total_balance')
    def _compute_sum_total_balance(self):
        for move in self:
            # Find all moves with the same partner created before the current move
            moves_with_same_partner = self.env['account.move'].search([
                ('partner_id', '=', move.partner_id.id),
                ('id', '<=', move.id),
            ])

            # Calculate the total balance sum for all moves with the same partner
            total_balance_sum = sum(moves_with_same_partner.mapped('total_balance'))

            # Update the sum_total_balance for all previous moves
            for prev_move in moves_with_same_partner:
                prev_move.sum_total_balance = total_balance_sum

    @api.model
    def create(self, vals):
        # Call the original create method
        move = super(AccountMove, self).create(vals)

        # Subtract amount_total from sum_total_balance
        if move.partner_id:
            moves_with_same_partner = self.env['account.move'].search([
                ('partner_id', '=', move.partner_id.id),
                ('id', '<=', move.id),
            ])

            for prev_move in moves_with_same_partner:
                prev_move.sum_total_balance -= move.amount_total

        return move



''''
    @api.depends('total_balance')
    def _compute_sum_total_balance(self):
        for move in self:
            # Filter account moves based on the partner_id
            moves_with_same_partner = self.env['account.move'].search([
                ('partner_id', '=', move.partner_id.id),
            ])

            # Calculate the total_balance for the filtered account moves
            total_balance_sum = sum(moves_with_same_partner.mapped('total_balance'))

            # Update the sum_total_balance for the current account move
            move.sum_total_balance = total_balance_sum
'''




class SaleOrder(models.Model):
    _inherit = "sale.order"
    #--------------------------------------------------------------
    #We add total_multiplied_field to sale order which  comput sum for total multiple field that is defid already in sales order line.

    total_multiplied_field = fields.Float('Total Multiplied Field', compute='_compute_total_multiplied_field',
                                          store=True, readonly=True)

    @api.model
    @api.depends('order_line.multiplied_field')
    def _compute_total_multiplied_field(self):
        for order in self:
            total_before_tax = sum(order.order_line.mapped('multiplied_field'))
            tax_percentage = 0.15  # 15% tax

            # Calculate the total including tax
            order.total_multiplied_field = total_before_tax * (1 + tax_percentage)
    #-----------------------------------------------------------------------
