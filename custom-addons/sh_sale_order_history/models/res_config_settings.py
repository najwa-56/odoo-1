# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    sh_sale_configuration_limit = fields.Integer(
        string="Last No. of Orders", default=0)
    enable_reorder = fields.Boolean("Enable Reorder")
    day = fields.Integer(
        string="Last No. of Day's Orders", default=0)
    stages = fields.Many2many('sale.order.stages',string="Stages")
    

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sh_sale_configuration_limit = fields.Integer(string="Last No. of Orders",
        related='company_id.sh_sale_configuration_limit', readonly=False
    )
    enable_reorder = fields.Boolean(
        "Enable Reorder", related="company_id.enable_reorder", readonly=False)
    day = fields.Integer(
        "Last No. of Day's Orders", related="company_id.day", readonly=False)
    stages = fields.Many2many('sale.order.stages',string="Stages",related="company_id.stages", readonly=False)
