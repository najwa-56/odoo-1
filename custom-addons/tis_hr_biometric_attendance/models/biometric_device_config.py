# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.
import base64
from odoo import api, fields, models, _
from collections import defaultdict
from odoo.addons.base.models.res_partner import _tz_get
import pytz
from datetime import datetime
from ..zk import ZK
from odoo.exceptions import UserError, ValidationError
import re


class BiometricDeviceConfig(models.Model):
    _name = 'biometric.config'
    _description = 'biometric config'

    name = fields.Char(string='Name', required=True)
    device_ip = fields.Char(string='Device IP')
    port = fields.Integer(string='Port')
    is_password_set = fields.Boolean(string='Is Password Set', default=False)
    device_password = fields.Char(string='Device Password', null=True, blank=True)
    time_zone = fields.Selection(_tz_get, string='Timezone', default=lambda self: self.env.user.tz or 'GMT')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, readonly=True)
    delay = fields.Integer("Delay", default=10)
    error_delay = fields.Integer("Delay",
                                 default=30)
    real_time = fields.Boolean("Real Time")
    trans_interval = fields.Integer("Trans Interval", default=2)
    is_adms = fields.Boolean('ADMS')
    serial_number = fields.Char('Serial Number')
    biometric_attendance_user_ids = fields.One2many('biometric.attendance.devices',
                                                    'device_id',
                                                    'Users')
    op_stamp_log_ids = fields.One2many('op.stamp.log',
                                                    'device_id',
                                                    'Op Stamp Logs')
    stamp_log_ids = fields.One2many('stamp.log',
                                                    'device_id',
                                                    'Stamp Log')
    attendance_log_count = fields.Integer(
        string='Attendance Logs',
        compute='_compute_attendance_log_count'
    )
    command_count = fields.Integer(
        string='Command Count',
        compute='_compute_command_count_count'
    )
    state = fields.Selection([('not_connected', 'Not Connected'),
                              ('connected', 'Connected')],
                             default='not_connected')
    attendance_status_ids = fields.One2many('attendance.state',
                                            "device_id",
                                            "Attendance States")

    tz_num = fields.Char(
        string='Timezone',
        compute='_compute_tz_num',
        store=True
    )

    @api.onchange('is_password_set')
    def on_is_password_set_change(self):
        if not self.is_password_set:
            self.device_password = ''

    @api.depends('time_zone')
    def _compute_tz_num(self):
        for r in self:
            timezone = pytz.timezone(r.time_zone or 'GMT')
            r.tz_num = str(int(datetime.now(timezone).tzinfo.utcoffset(
                datetime.now(timezone)).total_seconds() / 3600))

    @api.constrains('is_adms')
    def _constrains_is_adms(self):
        if not self.attendance_status_ids:
            self.attendance_status_ids = [(0, 0, {'name': 'Check-In', 'code':1, 'activity_type':'check_in'}),
                              (0, 0, {'name': 'Check-Out', 'code':2, 'activity_type':'check_out'})]

    @api.onchange('device_password')
    def _check_password(self):
        if self.device_password and not self.device_password.isdigit():
            raise UserError(_("Device password should only contain numeric characters."))

    def test_device_connection(self):
        ip = self.device_ip
        port = self.port
        password = self.device_password
        zk = ZK(ip, port, password=password)
        try:
            conn = zk.connect()
            if conn:
                raise UserError(_("Connection Success"))
            else:
                raise ValidationError(_("Connection Failed"))
        except Exception as e:
            # print(e)
            raise UserError(_(e))

    def sync_employees(self):
        uid = 0
        employees = self.env['hr.employee'].search([])
        next_user_id = 1
        uid_list = []
        user_id_list = []
        ip = self.device_ip
        port = self.port
        password = self.device_password
        zk = ZK(ip, port, password=password)
        try:
            conn = zk.connect()
            if conn:
                users = zk.get_users()
                print("USERS",users)
                def create_next_user_id(user_id):
                    pattern = r'(\d+)'

                    # Find the number and increment it by a specific value
                    def increment(match):
                        number = match.group(0)
                        incremented_number = str(int(number) + 1)  # Increment by 20
                        return incremented_number

                    # Replace the number in the original string
                    c_user_id = re.sub(pattern, increment, user_id)
                    return c_user_id

                if users:
                    for user in users:
                        uid_list.append(user.uid)
                        user_id_list.append(user.user_id)
                    uid_list.sort()
                    user_id_list.sort()
                    uid = uid_list[-1]
                    user_id = str(user_id_list[-1])
                    next_user_id = create_next_user_id(user_id)
                    num = 2
                    while 1:
                        if next_user_id in user_id_list:
                            user_id = str(user_id_list[-1 * num])
                            next_user_id = create_next_user_id(user_id)
                            num += 1
                        else:
                            for i in range(len(employees)):
                                test_user_id = create_next_user_id(next_user_id)
                                if test_user_id in user_id_list:
                                    next_user_id = test_user_id
                                    continue
                            break
                for employee in employees:
                    biometric_device = employee.biometric_device_ids.search(
                        [('employee_id', '=', employee.id), ('device_id', '=', self.id)])
                    if not biometric_device:
                        uid += 1
                        employee.biometric_device_ids = [(0, 0, {
                            'employee_id': employee.id,
                            'biometric_attendance_id': next_user_id,
                            'device_id': self.id,
                        })]
                        zk.set_user(uid, employee.name, 0, '', '', str(next_user_id))
                        next_user_id = create_next_user_id(next_user_id)
                return {'name': 'Success Message',
                        'type': 'ir.actions.act_window',
                        'res_model': 'employee.sync.wizard',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'target': 'new'}
            else:
                raise ValidationError("Connection Failed")
        except Exception as e:
            raise UserError(_(e))

    def download_attendance_log(self):
        attend_obj = self.env['attendance.log']
        ip = self.device_ip
        port = self.port
        password = self.device_password
        zk = ZK(ip, port, password=password)
        try:
            conn = zk.connect()
            if conn:
                attendances = zk.get_attendance()
                conn.disconnect()
                device = self.name
                company_id = self.company_id
                if attendances:
                    attendence_list = []
                    for attendance in attendances:
                        # attendence_dict = {}
                        atten_time = attendance.timestamp
                        atten_time = datetime.strptime(
                            atten_time.strftime('%Y-%m-%d %H:%M:%S'),
                            '%Y-%m-%d %H:%M:%S')
                        local_tz = pytz.timezone(self.time_zone or 'GMT')
                        local_dt = local_tz.localize(atten_time, is_dst=None)
                        utc_dt = local_dt.astimezone(pytz.utc)
                        utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                        atten_time = datetime.strptime(utc_dt,
                                                       "%Y-%m-%d %H:%M:%S")
                        atten_time = fields.Datetime.to_string(atten_time)
                        employees = self.env[
                            'biometric.attendance.devices'].search(
                            [('biometric_attendance_id', '=',
                              attendance.user_id),
                             ('device_id', '=', self.id)])
                        if len(employees) > 1:
                            employee_id = employees.mapped('employee_id')
                            employee_name = employee_id.mapped('name')
                            raise UserError(
                                _("Two Users have same Biometric User ID %s ") % employee_name)
                        if employees:
                            attendence_dict = {
                                'device_user_id': employees.id,
                                'user_id': attendance.user_id,
                                'atten_time': atten_time,
                                'employee_id': employees.employee_id.id
                            }
                            attendence_list.append(attendence_dict)
                    employee_status = defaultdict(list)
                    sorted_attendance = sorted(attendence_list, key=lambda x: (x['user_id'], x['atten_time']))
                    for entry in sorted_attendance:
                        user_id = entry['user_id']
                        employee_id = entry['employee_id']
                        entry_time = entry['atten_time']
                        atten_time = datetime.strptime(entry['atten_time'],
                                                       '%Y-%m-%d %H:%M:%S')
                        if not employee_status[user_id]:
                            employee_status[user_id].append(
                                {'status': 'Check-in', 'time': atten_time,
                                 'employee_id': employee_id,
                                 'entry_time': entry_time
                                 })
                            entry['status'] = 'Check-in'
                        else:
                            if atten_time > employee_status[user_id][-1]['time']:
                                current_status = 'Check-out' if employee_status[user_id][-1]['status'] == 'Check-in' else 'Check-in'
                                employee_status[user_id].append(
                                    {'status': current_status, 'time': atten_time,'employee_id': employee_id,
                                 'entry_time': entry_time})
                                entry['status'] = current_status
                        existing_log = attend_obj.search(
                            [('employee_id', '=', employee_id),
                             ('punching_time', '=', entry_time)])
                        if existing_log:
                            for log in existing_log:
                                if log.is_calculated == True:
                                    if entry['status'] == 'Check-in':
                                        attendance_status = '0'
                                    elif entry['status'] == 'Check-out':
                                        attendance_status = '1'
                                    vals = {
                                        'employee_id': employee_id,
                                        'punching_time': entry_time,
                                        'status': attendance_status,
                                        'device': str(device),
                                        'company_id': company_id.id,
                                        'is_calculated': True}
                                else:
                                    if entry['status'] == 'Check-in':
                                        attendance_status = '0'
                                    elif entry['status'] == 'Check-out':
                                        attendance_status = '1'
                                    vals = {
                                        'employee_id': employee_id,
                                        'punching_time': atten_time,
                                        'status': attendance_status,
                                        'device': str(device),
                                        'company_id': company_id.id,
                                        'is_calculated': False}
                                existing_log.write(vals)
                        else:
                            if entry['status'] == 'Check-in':
                                attendance_status = '0'
                            elif entry['status'] == 'Check-out':
                                attendance_status = '1'
                            vals = {'employee_id': employee_id,
                                    'punching_time': atten_time,
                                    'status': attendance_status,
                                    'device_user_id': entry['device_user_id'],
                                    'device': str(device),
                                    'company_id': company_id.id,
                                    'is_calculated': False}
                            attend_obj.create(vals)
                    return {'name': 'Success Message',
                            'type': 'ir.actions.act_window',
                            'res_model': 'success.wizard',
                            'view_mode': 'form',
                            'view_type': 'form',
                            'target': 'new'}
            else:
                raise ValidationError("Connection failed")
        except Exception as e:
            raise UserError(_(e))

    def download_attendance_log_new(self):
        devices = self.env["biometric.config"].search([])
        for device in devices:
            if device.is_adms:
                device.download_attendance_log()

 # ----------------------ADMS FUNCTIONS--------------------------------

 # Adjust if necessary (e.g., if device name is used for logs)
    def _compute_attendance_log_count(self):
        """Compute the number of attendance logs for this device."""
        for device in self:
            device.attendance_log_count = self.env[
                'attendance.data.log.device'].search_count([
                ('device_id', '=', device.id)
            ])
    def _compute_command_count_count(self):
        """Compute the number of attendance logs for this device."""
        for device in self:
            device.command_count = self.env[
                'device.command'].search_count([
                ('device_id', '=', device.id)
            ])

    def action_open_device_logs(self):
        """This method returns an action that displays the attendance data log records
           filtered by the current device (self)."""
        self.ensure_one()  # Make sure only one record is being processed

        return {
            'type': 'ir.actions.act_window',
            'name': 'Attendance Data Logs',
            'view_mode': 'tree,form',
            'res_model': 'attendance.data.log.device',
            'domain': [('device_id', '=', self.id)],
            # Filter by the current device
            'context': dict(self.env.context, default_device_id=self.id),
        }

    def action_open_finger_prints(self):
        """This method returns an action that displays the attendance data log records
           filtered by the current device (self)."""
        self.ensure_one()  # Make sure only one record is being processed

        return {
            'type': 'ir.actions.act_window',
            'name': 'Attendance Data Logs',
            'view_mode': 'tree,form',
            'res_model': 'finger.template',
            'domain': [('device_id', '=', self.id)],
            # Filter by the current device
            'context': dict(self.env.context, default_device_id=self.id),
        }

    def action_open_commands(self):
        """This method returns an action that displays the attendance data log records
           filtered by the current device (self)."""
        self.ensure_one()  # Make sure only one record is being processed

        return {
            'type': 'ir.actions.act_window',
            'name': 'Command To Device',
            'view_mode': 'tree,form',
            'res_model': 'device.command',
            'domain': [('device_id', '=', self.id)],
            # Filter by the current device
            'context': dict(self.env.context, default_device_id=self.id),
        }

    def create_oplog(self, values, OpStamp):
        date_object = datetime.strptime(f"{values[3]} {values[4]}",
                                        "%Y-%m-%d %H:%M:%S")
        local_tz = pytz.timezone('Asia/Kolkata')
        local_dt = local_tz.localize(date_object)
        # Convert the local time to UTC
        utc_dt = local_dt.astimezone(pytz.utc)
        formatted_utc_dt = utc_dt.strftime('%Y-%m-%d %H:%M:%S')
        operation_log = self.env[
            'attendance.data.log.device'].sudo().create({
            'device_id': self.id,
            'log_code': values[1],
            'description': values[1],
            'operator': values[2],
            'op_time': formatted_utc_dt,
            'value_1': values[5],
            'value_2': values[6],
            'value_3': values[7],
            'reserved': values[8],
            'opStamp': OpStamp,
        })

    def create_device_user(self, values):
        user_device_id = values[1].split('=')[1]
        user_device_name = values[2].split('=')[1]
        device_user_id = self.env['biometric.attendance.devices'].sudo().search([
            ('biometric_attendance_id', '=', user_device_id),
            ('device_id', '=', self.id)
        ])
        if device_user_id:
            device_user_id.device_user_name = user_device_name
        else:
            device_user_id = self.env['biometric.attendance.devices'].sudo().create({
                'biometric_attendance_id':user_device_id,
                'device_id':self.id,
                'device_user_name':user_device_name
            })
        return device_user_id

    def create_att_log(self, raw_data):
        for line in raw_data.splitlines():
            # Split the line by spaces to extract fields
            # user_device_id, date, time, number, status_code = line.split()
            values = line.split()
            user_device_id = values[0]
            date = values[1]
            time = values[2]
            status_code = values[3]
            number = values[4]
            db_user_device_id = self.env['biometric.attendance.devices'].sudo().search([
                ('biometric_attendance_id', '=', user_device_id),
                ('device_id', '=', self.id)])
            if not db_user_device_id:
                db_user_device_id = self.env['biometric.attendance.devices'].create({
                    'biometric_attendance_id': user_device_id,
                    'device_id': self.id
                })
            # status_map = {
            #     0: '0',
            #     2: 'check_in',
            #     1: 'check_out',  # Assuming 1 represents check_out
            #     101: '101'  # Add other mappings if needed (for 101, etc.)
            # }
            # # Convert the status_code to an integer
            status_code = int(status_code)
            # Find the user by device_id
            date_object = datetime.strptime(f"{date} {time}",
                                            "%Y-%m-%d %H:%M:%S")
            local_tz = pytz.timezone(self.time_zone)
            local_dt = local_tz.localize(date_object)
            # Convert the local time to UTC
            utc_dt = local_dt.astimezone(pytz.utc)
            timestamp = date_object.timestamp()
            formatted_utc_dt = utc_dt.strftime('%Y-%m-%d %H:%M:%S')
            # Get timestamp
            attendance_exist = (self.env['attendance.log'].
                                sudo().search(
                [('device_user_id', '=', db_user_device_id.id),
                 ('timestamp', '=', timestamp)]))
            att_status_id = self.env['attendance.state'].search([
                ('code', '=', status_code), ('device_id', '=', self.id)], limit=1)
            att_status = False
            if att_status_id:
                if att_status_id.activity_type == 'check_in':
                    att_status = '0'
                elif att_status_id.activity_type == 'check_out':
                    att_status = '1'
                else:
                    att_status = '2'
            else:
                att_status = '2'
            if not attendance_exist:
                test = self.env['attendance.log'].sudo().create({
                    'device_user_id': db_user_device_id.id,
                    'company_id': self.company_id.id,
                    'punching_time': formatted_utc_dt,
                    'status_number': status_code,
                    'number': number,
                    'status': att_status,
                    'device': self.name,
                    'timestamp': timestamp,
                    # 'status_string':status_map[status_code]
                })

    def create_finger_print(self, values):
        device_user_id = values[1].split('=')[1]
        fp_temp = values[5].split('=')[1]
        tmp = self._fix_base64_padding(fp_temp)
        db_user_device_id = self.env[
            'biometric.attendance.devices'].sudo().search(
            [('biometric_attendance_id', '=', device_user_id)])
        if not db_user_device_id:
            db_user_device_id = self.env[
                'biometric.attendance.devices'].sudo().create({
                'biometric_attendance_id': device_user_id,
                'device_id': self.id
            })
        fp_exist = self.env['finger.template'].sudo().search([('device_id', '=', self.id),
                                                       ('device_user_id', '=', db_user_device_id.id)])
        if fp_exist:
            fp_exist.template_data = tmp
        else:
            fp_id = self.env[
                'finger.template'].sudo().create({
                'device_user_id': db_user_device_id.id,
                'device_id': self.id,
                'template_data':tmp
            })


    def _fix_base64_padding(self, base64_string):
        """Ensure that the base64 string has the correct padding for decoding."""
        missing_padding = len(base64_string) % 4
        if missing_padding:
            base64_string += '=' * (4 - missing_padding)
        binary_data = base64.b64decode(base64_string)
        return base64.b64encode(binary_data)

    def create_user_command(self):
        command_ids = self.env['device.command'].sudo().search([('status', '=', 'pending'),
                                                                ('device_id', '=', self.id)])
        command = ""
        for command_id in command_ids:
            command += command_id.execution_log
            command_id.status = 'executed'
        return command

    def check_user_command_response(self, command_id):
        if command_id:
            command_exist = self.env['device.command'].search([('id', '=', command_id)])
            if command_exist:
                if command_exist.employee_id and command_exist.name == "DATA":
                    values = command_exist.execution_log.split()
                    user_device_id = values[2].split('=')[1]
                    user_device_name = values[3].split('=')[1]
                    device_user_id = self.env[
                        'biometric.attendance.devices'].sudo().search([('biometric_attendance_id', '=', user_device_id),
                                                                       ('device_id', '=', self.id)])
                    if not device_user_id:
                        device_user_id = self.env[
                            'biometric.attendance.devices'].sudo().create({
                            'biometric_attendance_id': user_device_id,
                            'device_id': self.id,
                            'device_user_name': user_device_name,
                            'employee_id': command_exist.employee_id.id,
                        })
                        command_exist.status = 'success'
                    else:
                        device_user_id.employee_id = command_exist.employee_id
                        device_user_id.device_user_name = command_exist.employee_id.name
                        command_exist.status = 'success'
                elif command_exist.employee_id and command_exist.name == "DEL":
                    values = command_exist.execution_log.split()
                    user_device_id = values[2].split('=')[1]
                    device_user_id = self.env[
                        'biometric.attendance.devices'].sudo().search(
                        [('biometric_attendance_id', '=', user_device_id),
                         ('device_id', '=', self.id)])
                    device_user_id.unlink()
                    command_exist.status = 'success'
                elif command_exist.employee_id and command_exist.name == "UPDATE":
                    device_user_id = self.env[
                        'biometric.attendance.devices'].sudo().search(
                        [('biometric_attendance_id', '=', command_exist.pin),
                         ('device_id', '=', self.id)])
                    device_user_id.device_user_name = command_exist.employee_id.name
                    command_exist.status = 'success'
                elif command_exist.name == "USERINFO" or command_exist.name == 'CHECK':
                    command_exist.status = 'success'
            return command_exist

    def export_employee(self):
        employee_ids = self.env['hr.employee'].search([])
        for employee_id in employee_ids:
            device_user = employee_id.biometric_device_ids.filtered(
                lambda x: x.device_id == self)
            if not device_user:
                employee_id.create_export_command(self)

    def download_device_users(self):
        command_id = self.env['device.command'].sudo().search(
            [('device_id', '=', self.id),
             ('name', '=', 'USERINFO'),
             ('status', '=', 'pending')])
        if not command_id:
            command_id = self.env['device.command'].sudo().create({
                'name': 'USERINFO',
                'device_id': self.id,
                'status': 'pending',
            })
            command_id.execution_log = f"C:{command_id.id}:DATA QUERY USERINFO\n"

    def check_connection(self):
        command_id = self.env['device.command'].sudo().search(
            [('device_id', '=', self.id),
             ('name', '=', 'CHECK'),
             ('status', '=', 'pending')])
        if not command_id:
            command_id = self.env['device.command'].sudo().create({
                'name': 'CHECK',
                'device_id': self.id,
                'status': 'pending',
            })
            command_id.execution_log = f"C:{command_id.id}:CHECK\n"