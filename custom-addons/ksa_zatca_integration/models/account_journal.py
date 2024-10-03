
from odoo import api, fields, models, exceptions, _
class account_journal(models.Model):
    _inherit = "account.journal"

    cr = fields.Char('CR')
    branch_name = fields.Char('Branch Name')
    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    district = fields.Char('Destirct')
    city = fields.Char('city')
    street = fields.Char('Street')
    zip = fields.Char('Street')
    license = fields.Selection([('CRN', 'Commercial Registration number'),
                                ('MOM', 'Momrah license'), ('MLS', 'MHRSD license'),
                                ('SAG', 'MISA license'), ('OTH', 'Other OD'),
                                ('700', '700 Number')],
                               required=0, string="License",
                               help="In case multiple IDs exist then one of the above must be entered")
    license_no = fields.Char(string="License Number (Other seller ID)", required=0)

    building_no = fields.Char()
    additional_no = fields.Char()

