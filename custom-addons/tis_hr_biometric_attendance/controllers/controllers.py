from odoo import http
from odoo.http import request, Response
import logging
# from werkzeug.wrappers import Response
import time
from datetime import datetime
import json
import re
import pytz
_logger = logging.getLogger(__name__)

class ZKTecoController(http.Controller):

    @http.route('/iclock/cdata', type='http', auth='public', methods=['GET'])
    def zkteco_cdata(self, **kwargs):
        # Fetch parameters from the GET request
        sn = kwargs.get('SN')
        options = kwargs.get('options')
        pushver = kwargs.get('pushver')
        language = kwargs.get('language')
        device_id = request.env['biometric.config'].sudo().search([
            ('serial_number','=',sn)])
        if device_id:
            _logger.info(options)
            _logger.info(sn)
            _logger.info(pushver)
            _logger.info(language)
            _logger.info('updatedddddd')
            device_id.sudo().state = 'connected'
            ts = int(time.time())
            now = datetime.now()
            fixed_time = "00:00"
            # Current time for the second part
            current_time = now.strftime("%H:%M")
            # Combine both parts
            formatted_time = f"{fixed_time};{current_time}"
            operation_log = request.env['op.stamp.log'].sudo().search([])
            attendance_log_ids = request.env['stamp.log'].sudo().search([])

            if operation_log:
                opStamp = operation_log.sorted('opStamp')[-1].opStamp
            else:
                opStamp = 0
            if attendance_log_ids:
                stamp = attendance_log_ids.sorted('stamp')[-1].stamp
            else:
                stamp = 0
            response = (
                f"GET OPTION FROM: {sn}\n"
                f"Stamp={stamp}\n"
                f"OpStamp={opStamp}\n"
                f"ErrorDelay={device_id.error_delay}\n"
                f"Delay={device_id.delay}\n"
                f"TransTimes=00:00; 12:00\n"
                f"TransInterval={device_id.trans_interval}\n"
                f"TransFlag={1101111000}\n"
                f"TimeZone={device_id.tz_num}\n"
                f"Realtime={1}\n"
                f"Encrypt={0}\n"
            )
            return Response(response)
        return Response("Device not available in server", 405)

    @http.route('/iclock/cdata', type='http', auth='none', methods=['POST'],
                csrf=False)
    def receive_device_data(self, **kwargs):
        """
        Endpoint to receive data from the device.
        Expects JSON data in the request body.
        """
        serial_number = kwargs.get('SN')
        Stamp = kwargs.get('Stamp')
        OpStamp = kwargs.get('OpStamp')
        table = kwargs.get('table')
        stamp_val = Stamp if Stamp else OpStamp
        raw_data = http.request.httprequest.data.decode('utf-8')

        _logger.info(f"raw_data_28888888889 :  {raw_data}")
        device_id = request.env['biometric.config'].sudo().search([
            ('serial_number', '=', serial_number)])
        if device_id:
            if serial_number and table == "OPERLOG":
                _logger.info(raw_data)
                self.create_op_stamp_log (raw_data, device_id, stamp_val)
                for line in raw_data.strip().split('\n'):
                    if line.startswith("OPLOG"):
                        values = line.split()
                        try:
                            device_id.create_oplog(values, stamp_val)
                        except Exception as e:
                            _logger.info(f"ERROR :  {e}")
                    elif line.startswith("FP"):
                        values = line.split()
                        device_id.create_finger_print(values)
                    elif line.startswith("USER"):
                        values = line.split()
                        device_id.create_device_user(values)
            if serial_number and table == "ATTLOG":
                self.create_stamp_log(raw_data, device_id, stamp_val)
                _logger.info(f"raw_data_1010101010 :  {raw_data}")
                device_id.create_att_log(raw_data)

        # Check if the required parameters are present
        # if not serial_number or not timestamp:
        #     return "Error: Missing parameters", 400

        # Get the raw data from the POST request

        # # Split the data into records
        # records = raw_data.strip().split('\r\n')
        # _logger.info(f"recordsssssssssssssssssssssss {records}")


        # Process each record
        return Response("OK", 200)

    @http.route('/iclock/getrequest', type='http', auth='public',
                methods=['GET'], csrf=False)
    def get_request(self, **kwargs):
        # Return a placeholder response for the device commands
        serial_number = kwargs.get('SN')
        device_id = request.env['biometric.config'].sudo().search([
            ('serial_number', '=', serial_number)])
        command = device_id.create_user_command()
        _logger.info(f"commanddd :  {command}")
        if command == "":
            return Response("OK", 200)
        else:
            return Response(command, 200)

    @http.route('/iclock/devicecmd', type='http', auth='public',
                methods=['POST'], csrf=False)
    def device_command(self, **kwargs):
        # Placeholder: update command status if necessary (no command model used)
        raw_data = http.request.httprequest.data.decode('utf-8')
        _logger.info(f"devicecmd Raw Data :  {raw_data}")
        serial_number = kwargs.get('SN')
        device_id = request.env['biometric.config'].sudo().search([
            ('serial_number', '=', serial_number)])
        for line in raw_data.split('\n'):
            params =  line.split('&')
            param_dict = {}
            for param in params:
                if param:
                    key, value = param.split("=")
                    param_dict[key] = value
            if param_dict.get("CMD") == "DATA" or param_dict.get("CMD") == "CHECK":
                command_id = param_dict.get("ID")
                device_id.check_user_command_response(command_id)
        return Response("OK", 200)

    def create_op_stamp_log(self, raw_data, device_id, opStamp):
        op_stamp_log = request.env['op.stamp.log'].sudo().create({
            'log_text':raw_data,
            'device_id': device_id.id,
            'opStamp': opStamp
        })
    def create_stamp_log(self, raw_data, device_id, Stamp):
        op_stamp_log = request.env['stamp.log'].sudo().create({
            'log_text':raw_data,
            'device_id': device_id.id,
            'stamp': Stamp
        })
