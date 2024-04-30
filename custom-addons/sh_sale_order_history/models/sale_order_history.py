# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models, api
from dateutil.relativedelta import relativedelta
from datetime import datetime


class SaleOrderStges(models.Model):
    _name = "sale.order.stages"
    _description = "Sale Order Stages"

    sequence = fields.Integer(string="Sequence")
    name = fields.Char(required=True, translate=True, string="Name")
    color = fields.Integer(string="Color", default=1)
    stage_key = fields.Char(required=True, translate=True, string="Stage Keys")

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Stage name already exists !"),
    ]
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)


class SaleOrderHistory(models.Model):
    _name = "sale.order.history"
    _description = "Sale Order History"
    _order = "date_order desc"

    sale_reorder = fields.Boolean("Reorder")
    name = fields.Many2one("sale.order.line", "Sale Order Line")
    order_id = fields.Many2one(
        "sale.order",
        "Current Sale Order",
        readonly=True
    )
    status = fields.Selection(
        string="Status", related="name.order_id.state", readonly=True, store=True)
    #we add stor=True for status
    date_order = fields.Datetime("Date", )
    so_id = fields.Char("Sale Order")
    product_id = fields.Many2one(
        "product.product",
        related="name.product_id",
        readonly=True,

         # we Add this line to store the related field value in the database
        store=True,

    )
    pricelist_id = fields.Many2one(
        "product.pricelist",
        related="name.order_id.pricelist_id",
        readonly=True
    )
    price_unit = fields.Float(
        "Price",
        related="name.price_unit",
        readonly=True
    )
    new_price_unit = fields.Float(
        "New Price",
        compute='_compute_new_unit_price',
        readonly=True
    )
    product_uom_qty = fields.Float(
        "Quantity",
        related="name.product_uom_qty",
        readonly=True
    )
    discount = fields.Float('Discount',
                            related='name.discount',
                            readonly=True)
    product_uom = fields.Many2one(
        "uom.uom",
        "Unit",
        related="name.product_uom",
        readonly=True
    )
    currency_id = fields.Many2one(
        "res.currency",
        "Currency Id",
        related="name.currency_id"
    )
    price_subtotal = fields.Monetary(
        "Subtotal",
        readonly=True,
        related="name.price_subtotal"
    )
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    enable_reorder = fields.Boolean(
        "Enable Reorder Button for Sale Order History", related="company_id.enable_reorder")

    @api.depends('order_id.pricelist_id')
    def _compute_new_unit_price(self):

        for record in self:
            sh_new_price = 0.0
            if record.order_id and record.order_id.pricelist_id and record.product_id and record.order_id.partner_id and record.product_uom:
                price = record.order_id.pricelist_id._compute_price_rule(
                    record.product_id, record.product_uom_qty, uom_id=record.product_uom.id)
                sh_new_price = price.get(record.product_id.id)[0]
            record.new_price_unit = sh_new_price

    # Reorder Button

    def sales_reorder(self):
        vals = {
            "price_unit": self.price_unit,
            "product_uom_qty": self.product_uom_qty,
            "price_subtotal": self.price_subtotal
        }

        if self.product_id:
            vals.update({
                "name": self.product_id.display_name,
                "product_id": self.product_id.id
            })

        if self.product_uom:
            vals.update({"product_uom": self.product_uom.id})


        # context = self._context.get('params')
        # vals.update({"order_id": context.get('id')})

        so = self.env['sale.order'].sudo().browse(self.order_id.id)
        so.write({'order_line': [(0, 0, vals)]})
        so._cr.commit()

        return {"type": "ir.actions.client", "tag": "reload"}

    # View Sale Order Button

    def view_sales_reorder(self):

        return{
            'name': 'Sale Order',
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'current',
            'res_id': self.name.order_id.id,
        }


class SaleOrder(models.Model):
    _inherit = "sale.order"

   # we edit this filed
    # is_order_history_line_update = fields.Boolean(
     #   string='Update History Lines',
     #   compute='_compute_sale_order_history', store=True
   # )

    order_history_line = fields.One2many(
        "sale.order.history",
        "order_id",
        string="Order History",


        compute="_compute_sale_order_history",   # we edit this filed

    )

    enable_reorder = fields.Boolean(
        "Enable Reorder Button for Sale Order History", related="company_id.enable_reorder")

    # All Lines Reorder Button

    def action_all_sale_reorder(self):
        selected_sale_reorder_obj = self.order_history_line.filtered(lambda r: r.sale_reorder)

        if selected_sale_reorder_obj:
            for rec in selected_sale_reorder_obj:
                if self.enable_reorder:
                    vals = {
                        "price_unit": rec.price_unit,
                        "product_uom_qty": rec.product_uom_qty,
                        "price_subtotal": rec.price_subtotal
                    }

                    if rec.product_id:
                        vals.update({
                            "name": rec.product_id.display_name,
                            "product_id": rec.product_id.id
                        })

                    if rec.product_uom:
                        vals.update({"product_uom": rec.product_uom.id})

                    if self.id:
                        vals.update({'order_id': self.id})

                    self.write({'order_line': [(0, 0, vals)]})
                    self._cr.commit()
        else:

            for rec in self.order_history_line:
                if self.enable_reorder:
                    vals = {
                        "price_unit": rec.price_unit,
                        "product_uom_qty": rec.product_uom_qty,
                        "price_subtotal": rec.price_subtotal
                    }

                    if rec.product_id:
                        vals.update({
                            "name": rec.product_id.display_name,
                            "product_id": rec.product_id.id
                        })

                    if rec.product_uom:
                        vals.update({"product_uom": rec.product_uom.id})

                    if self.id:
                        vals.update({'order_id': self.id})

                    self.write({'order_line': [(0, 0, vals)]})
                    self._cr.commit()

        return {"type": "ir.actions.client", "tag": "reload"}

    @api.onchange("partner_id")
    def _onchange_partner(self):
        self.order_history_line = None
        if self.partner_id:
            partners = []
            domain = []

            partners.append(self.partner_id.id)

            if self.env.company.day:
                day = self.env.company.day
                Display_date = datetime.today() - relativedelta(days=day)
                domain.append(("date_order", ">=", Display_date),)

            stages = []

            if self.env.company.stages:
                for stage in self.env.company.stages:
                    if stage.stage_key:
                        stages.append(stage.stage_key)
                domain.append(("state", "in", stages))

            if self.env.user.company_id.sh_sale_configuration_limit:
                limit = self.env.user.company_id.sh_sale_configuration_limit
            else:
                limit = None

            if self.partner_id.child_ids:
                for child in self.partner_id.child_ids:
                    partners.append(child.id)

            if partners:
                domain.append(("partner_id", "in", partners),)

            if self._origin:
                domain.append(("id", "!=", self._origin.id))

            sale_order_search = self.env["sale.order"].search(
                domain,
                limit=limit,
                order="date_order desc",)

            sale_ordr_line = []
            if sale_order_search:
                for record in sale_order_search:

                    if record.order_line:
                        for rec in record.order_line:

                            sale_ordr_line.append((0, 0, {
                                 "order_id":record.id,
                                "so_id": record.name,
                                "name": rec.id,
                                'date_order': record.date_order,
                                'discount': rec.discount,
                                "product_id": rec.product_id.id,
                                "pricelist_id": record.pricelist_id.id,
                                "price_unit": rec.price_unit,
                                "product_uom_qty": rec.product_uom_qty,
                                "product_uom": rec.product_uom.id,
                                "price_subtotal": rec.price_subtotal,
                                "status": rec.state,
                            }))
            self.order_history_line = sale_ordr_line

    def _compute_sale_order_history(self):
        for vals in self:
            vals.order_history_line = None

            # we edit this filed
            #  if vals.is_order_history_line_update:
             #   vals.is_order_history_line_update = False

            if vals.partner_id:
                partners = []
                domain = []

                partners.append(vals.partner_id.id)

                history_domain = []
                if self.env.company.day:
                    day = self.env.company.day
                    Display_date = datetime.today() - relativedelta(days=day)
                    domain.append(("date_order", ">=", Display_date),)
                    history_domain.append(("date_order", ">=", Display_date),)

                stages = []

                if self.env.company.stages:
                    for stage in self.env.company.stages:
                        if stage.stage_key:
                            stages.append(stage.stage_key)
                    domain.append(("state", "in", stages))
                    history_domain.append(("status", "in", stages))

                if self.env.user.company_id.sh_sale_configuration_limit:
                    limit = self.env.user.company_id.sh_sale_configuration_limit
                else:
                    limit = None

                if vals.partner_id.child_ids:
                    for child in vals.partner_id.child_ids:
                        partners.append(child.id)

                # if vals.partner_id.parent_id:
                #     partners.append(vals.partner_id.parent_id.id)
                #     for child in vals.partner_id.parent_id.child_ids:
                #         partners.append(child.id)

                if partners:
                    domain.append(("partner_id", "in", partners),)
                    history_domain.append(
                        ('order_id.partner_id', 'in', partners),)

                    # we edit this filed
                #if vals.id:


                  #  domain.append(("id", "!=", vals.id))

                sale_order_search = self.env["sale.order"].search(
                    domain,
                    limit=limit,
                    order="date_order desc",)

                history_domain.append(
                    ('order_id', 'in', sale_order_search.ids),)

                if sale_order_search:
                    for record in sale_order_search:
                        history_ids = self.env['sale.order.history'].sudo().search(
                            history_domain,
                            limit=limit,
                            order="date_order desc",
                        )
                        if record.order_line:
                            for rec in record.order_line:
                                if rec.id in history_ids.name.ids:

                                    # we edit this filed

                                    # if not vals.is_order_history_line_update:
                                      #  vals.is_order_history_line_update = True

                                    vals.order_history_line = [
                                        (6, 0, history_ids.ids)]
                                else:
                                    history_vals = {
                                        "order_id": record.id,
                                        "so_id": record.name,
                                        "name": rec.id,
                                        'date_order': record.date_order,
                                        'discount': rec.discount,
                                        "product_id": rec.product_id.id,
                                        "pricelist_id": record.pricelist_id.id,
                                        "price_unit": rec.price_unit,
                                        "product_uom_qty": rec.product_uom_qty,
                                        "product_uom": rec.product_uom.id,
                                        "price_subtotal": rec.price_subtotal,
                                        "status": rec.state,
                                    }
                                    self.env['sale.order.history'].sudo().create(
                                        history_vals)
