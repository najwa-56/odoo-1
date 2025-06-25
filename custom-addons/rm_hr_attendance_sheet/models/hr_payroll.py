# -*- coding: utf-8 -*-

##############################################################################
#    Copyright (c) 2021 CDS Solutions SRL. (http://cdsegypt.com)
#    Maintainer: Eng.Ramadan Khalil (<ramadan.khalil@cdsegypt.com>)
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    sheet_id = fields.Many2one(comodel_name="attendance.sheet", string="Attendance Sheet", required=False, )

    def _get_workday_lines(self):
        self.ensure_one()

        work_entry_obj = self.env['hr.work.entry.type']
        overtime_work_entry = work_entry_obj.search([('code', '=', 'ATTSHOT')])
        latin_work_entry = work_entry_obj.search([('code', '=', 'ATTSHLI')])
        absence_work_entry = work_entry_obj.search([('code', '=', 'ATTSHAB')])
        difftime_work_entry = work_entry_obj.search([('code', '=', 'ATTSHDT')])
        if not overtime_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Overtime With Code ATTSHOT'))
        if not latin_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Late In With Code ATTSHLI'))
        if not absence_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Absence With Code ATTSHAB'))
        if not difftime_work_entry:
            raise ValidationError(_(
                'Please Add Work Entry Type For Attendance Sheet Diff Time With Code ATTSHDT'))

        overtime = [{
            'name': "Overtime",
            'code': 'OVT',
            'work_entry_type_id': overtime_work_entry[0].id,
            'sequence': 30,
            'number_of_days': self.sheet_id.no_overtime,
            'number_of_hours': self.sheet_id.tot_overtime,
        }]
        absence = [{
            'name': "Absence",
            'code': 'ABS',
            'work_entry_type_id': absence_work_entry[0].id,
            'sequence': 35,
            'number_of_days': self.sheet_id.no_absence,
            'number_of_hours': self.sheet_id.tot_absence,
        }]
        late = [{
            'name': "Late In",
            'code': 'LATE',
            'work_entry_type_id': latin_work_entry[0].id,
            'sequence': 40,
            'number_of_days': self.sheet_id.no_late,
            'number_of_hours': self.sheet_id.tot_late,
        }]
        difftime = [{
            'name': "Difference time",
            'code': 'DIFFT',
            'work_entry_type_id': difftime_work_entry[0].id,
            'sequence': 45,
            'number_of_days': self.sheet_id.no_difftime,
            'number_of_hours': self.sheet_id.tot_difftime,
        }]
        worked_days_lines = overtime + late + absence + difftime
        return worked_days_lines

    def compute_sheet(self):
        if self.sheet_id:

            worked_day_lines = self._get_workday_lines()
            print("ffffffffffffffffff" , self.worked_days_line_ids)
            if len(self.worked_days_line_ids)<2:
                self.worked_days_line_ids = [(0, 0, x) for x in
                                             worked_day_lines]
            res = super(HrPayslip, self).compute_sheet()

            return res
        else:
            res = super(HrPayslip, self).compute_sheet()

            return res
