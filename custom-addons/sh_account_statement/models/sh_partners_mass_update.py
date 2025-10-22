# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class MassActionWizard(models.TransientModel):
    _name = "sh.partners.mass.update"
    _description = "Partners config Statement Mass Update"

    sh_partners_update = fields.Selection(
        [("add", "Add"), ("remove", "Remove")],
        string="Customer Overdue Statement Action",
        default="add",
    )
    sh_update_customers_ids = fields.Many2many(
        "res.partner", "res_sh_update_customers_ids", string="Customers"
    )
    sh_update_vendors_ids = fields.Many2many(
        "res.partner", "res_sh_update_vendors_ids", string="Vendors"
    )
    sh_statement_ids = fields.Many2many(
        "sh.statement.config", string="Statement Mass Update"
    )

    # update Partners
    def update_partners(self):
        if self.sh_partners_update == "add":
            if self.sh_update_customers_ids:
                for partner in self.sh_update_customers_ids:
                    for record in self.sh_statement_ids:
                        if partner not in record.sh_customer_partner_ids:
                            record.write({"sh_customer_partner_ids": [(4, partner.id)]})
            if self.sh_update_vendors_ids:
                for partner in self.sh_update_vendors_ids:
                    for record in self.sh_statement_ids:
                        if partner not in record.sh_vendor_partner_ids:
                            record.write({"sh_vendor_partner_ids": [(4, partner.id)]})
        else:
            if self.sh_update_customers_ids:
                for partner in self.sh_update_customers_ids:
                    for record in self.sh_statement_ids:
                        if partner in record.sh_customer_partner_ids:
                            record.sh_customer_partner_ids = [(3, partner.id)]
            if self.sh_update_vendors_ids:
                for partner in self.sh_update_vendors_ids:
                    for record in self.sh_statement_ids:
                        if partner in record.sh_vendor_partner_ids:
                            record.sh_vendor_partner_ids = [(3, partner.id)]
        if not self.sh_update_customers_ids and not self.sh_update_vendors_ids:
            raise UserError(
                _("Please select any Customers or Vendors to update statement..!")
            )


class MassActionpartnerWizard(models.TransientModel):
    _name = "sh.partners.config.mass.update"
    _description = "Partners Statement Mass Update"

    sh_partners_config_update = fields.Selection(
        [("add", "Add"), ("remove", "Remove")],
        string="Partners Statement Action",
        default="add",
    )
    sh_update_config_ids = fields.Many2many(
        "sh.statement.config", string="Config", required=True
    )
    sh_selected_partner_ids = fields.Many2many(
        "res.partner", string="Selected partners"
    )

    # Update Customers Statement Config
    def update_partners_config(self):
        if self.sh_partners_config_update == "add":
            for record in self.sh_update_config_ids:
                for partner in self.sh_selected_partner_ids:
                    if partner.customer_rank >= 1:
                        if partner not in record.sh_customer_partner_ids:
                            record.write({"sh_customer_partner_ids": [(4, partner.id)]})
                            partner.sh_customer_statement_config = [(4, record.id)]
                    if partner.supplier_rank >= 1:
                        if partner not in record.sh_vendor_partner_ids:
                            record.write({"sh_vendor_partner_ids": [(4, partner.id)]})
                            partner.sh_vendor_statement_config = [(4, record.id)]
        else:
            for record in self.sh_update_config_ids:
                for partner in self.sh_selected_partner_ids:
                    if partner.customer_rank >= 1:
                        if partner in record.sh_customer_partner_ids:
                            record.sh_customer_partner_ids = [(3, partner.id)]
                            partner.sh_customer_statement_config = [(3, record.id)]
                    if partner.supplier_rank >= 1:
                        if partner in record.sh_vendor_partner_ids:
                            record.sh_vendor_partner_ids = [(3, partner.id)]
                            partner.sh_vendor_statement_config = [(3, record.id)]
