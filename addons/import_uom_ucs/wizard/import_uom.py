# -*- coding: utf-8 -*-
from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
import io
import tempfile
import binascii
import logging
_logger = logging.getLogger(__name__)

try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')
try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')


class ImportUom(models.TransientModel):
    _name = 'import.uom'

    file = fields.Binary(string="File", required=True)
    file_name = fields.Char('File Name')

    def discard(self):
        ''

    def download_sample_attachment(self):
        attachment = self.env['ir.attachment'].sudo().search([('name', '=', 'sample_import_uom.xlsx'),
                                                              ('res_model', '=', 'import.uom')])
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % (attachment.id),
            'target': 'new',
            'nodestroy': False,
        }

    def import_xls(self):
        try:
            fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            values = {}
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
        except Exception as e:
            raise UserError(_("Invalid file ! "))

        dict_list = []
        keys = sheet.row_values(0)
        values = [sheet.row_values(i) for i in range(1, sheet.nrows)]

        for value in values:
            dict_list.append(dict(zip(keys, value)))

        for line in dict_list:
                uom_name = line.get('Name')

                if uom_name == '':
                    raise ValidationError(_("Value of Name cannot be null."))

                if line.get('Factor') == '' or line.get('Factor') == '0.0':
                   raise ValidationError(_(f"{uom_name} : Value of Factor cannot  be zero."))
                
                category_name = line.get('Categoty')

                if category_name == '':
                    raise ValidationError(_("Value of Category cannot be null."))

                category_id = self.env['uom.category'].search(
                    [('name', '=', line.get('Categoty'))], limit=1)

                if not category_id:
                    category_id = self.env['uom.category'].create({
                        'name': line.get('Categoty')
                    })

                if (line.get('Type') == 'Bigger than the reference Unit of Measure'):
                    type = 'bigger'
                elif (line.get('Type') == 'Reference Unit of Measure for this category'):
                    type = 'reference'
                elif (line.get('Type') == 'Smaller than the reference Unit of Measure'):
                    type = 'smaller'
                else:
                    type = 'none'

                type_name = line.get('Type')
                if type_name == '':
                    raise ValidationError(_("Value of Type cannot be null."))
                uom_id = self.env['uom.uom'].search([('name', '=', line.get('Name')),
                                                    ('uom_type', '=', type),
                                                    ('category_id', '=',
                                                        category_id.id)
                                                    ], limit=1)
                if not uom_id:
                    self.env['uom.uom'].create({
                        'name': line.get('Name'),
                        'category_id': category_id.id,
                        'uom_type': type,
                        'factor_inv': int(line.get('Factor'))
                    })
