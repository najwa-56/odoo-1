# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class IrActionsActWindow(models.Model):
    """Inheriting the 'ir.action.act.window' model."""
    _inherit = 'ir.actions.act_window'

    custom_report = fields.Char(string='Custom ID', help="Custom report")


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    uom_name = fields.Char(string="UOM Name")

    def _select(self):
        select_str = super(AccountInvoiceReport, self)._select()
        select_str += ", line.uom_name as uom_name"
        return select_str

    def _group_by(self):
        group_by_str = super(AccountInvoiceReport, self)._group_by()
        group_by_str += ", line.uom_name"
        return group_by_str