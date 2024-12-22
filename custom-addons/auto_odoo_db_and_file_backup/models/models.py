# -*- coding: utf-8 -*-
# imports of python libs
import datetime
import json
import os
import pytz
import shutil
import tempfile
import time

try:
    from xmlrpc import client as xmlrpclib
except ImportError:
    import xmlrpclib

import socket
import requests
from odoo.addons.google_account.models.google_service import GOOGLE_TOKEN_ENDPOINT, TIMEOUT
from odoo.tools import exec_pg_environ
import sys
import subprocess
from dateutil.relativedelta import relativedelta
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError
from dropbox import DropboxOAuth2FlowNoRedirect
import http.client
import ftplib
import pysftp
import boto3
from botocore.exceptions import ClientError
import paramiko
from paramiko.ssh_exception import SSHException
import base64
import io
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import logging

_logger = logging.getLogger(__name__)
# imports of odoo
import odoo
from odoo import models, fields, api, _
from odoo.exceptions import AccessDenied, RedirectWarning, UserError

_intervalTypes = {
    'days': lambda interval: relativedelta(days=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'weeks': lambda interval: relativedelta(days=7 * interval),
    'months': lambda interval: relativedelta(months=interval),
    'minutes': lambda interval: relativedelta(minutes=interval),
}


def execute(connector, method, *args):
    res = False
    try:
        res = getattr(connector, method)(*args)
    except socket.error as error:
        _logger.critical('Error while executing the method "execute". Error: ' + str(error))
        raise error
    return res


class IrCronInherit(models.Model):
    _inherit = "ir.cron"

    @classmethod
    def _process_job(cls, db, cron_cr, job):
        """ Execute a cron job and re-schedule a call for later. """

        # Compute how many calls were missed and at what time we should
        # recall the cron next. In the example bellow, we fake a cron
        # with an interval of 30 (starting at 0) that was last executed
        # at 15 and that is executed again at 135.
        #
        #    0          60          120         180
        #  --|-----|-----|-----|-----|-----|-----|----> time
        #    1     2*    *     *     *  3  4
        #
        # 1: lastcall, the last time the cron was executed
        # 2: past_nextcall, the cron nextcall as seen from lastcall
        # *: missed_call, a total of 4 calls are missing
        # 3: now
        # 4: future_nextcall, the cron nextcall as seen from now

        with cls.pool.cursor() as job_cr:
            lastcall = fields.Datetime.to_datetime(job['lastcall'])
            interval = _intervalTypes[job['interval_type']](job['interval_number'])
            env = api.Environment(job_cr, job['user_id'], {'lastcall': lastcall})
            ir_cron = env[cls._name]

            # Use the user's timezone to compare and compute datetimes,
            # otherwise unexpected results may appear. For instance, adding
            # 1 month in UTC to July 1st at midnight in GMT+2 gives July 30
            # instead of August 1st!
            now = fields.Datetime.context_timestamp(ir_cron, datetime.datetime.utcnow())
            past_nextcall = fields.Datetime.context_timestamp(
                ir_cron, fields.Datetime.to_datetime(job['nextcall']))

            # Compute how many call were missed
            missed_call = past_nextcall
            missed_call_count = 0
            while missed_call <= now:
                missed_call += interval
                missed_call_count += 1
            future_nextcall = missed_call

            # Compute how many time we should run the cron
            effective_call_count = (
                1 if not missed_call_count  # run at least once
                else 1 if not job['doall']  # run once for all
                else missed_call_count if job['numbercall'] == -1  # run them all
                else min(missed_call_count, job['numbercall'])  # run maximum numbercall times
            )
            call_count_left = max(job['numbercall'] - effective_call_count, -1)

            # The actual cron execution
            for call in range(effective_call_count):
                ir_cron._callback(job['cron_name'], job['ir_actions_server_id'], job['id'])

        # Update the cron with the information computed above
        cron_cr.execute("""
            UPDATE ir_cron
            SET nextcall=%s,
                numbercall=%s,
                lastcall=%s,
                active=%s
            WHERE id=%s
        """, [
            fields.Datetime.to_string(future_nextcall.astimezone(pytz.UTC)),
            call_count_left,
            fields.Datetime.to_string(now.astimezone(pytz.UTC)),
            job['active'] and bool(call_count_left),
            job['id'],
        ])

        # custom code
        with cls.pool.cursor() as job_cr:
            lastcall = fields.Datetime.to_datetime(job['lastcall'])
            cron = api.Environment(job_cr, job['user_id'], {'lastcall': lastcall})

            if job['id'] == cron.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_dropbox').id:
                bid = cron.ref('auto_odoo_db_and_file_backup.rule_upload_backup_to_dropbox').id
                cron_cr.execute("UPDATE database_backup SET next_exec_dt=%s" + " WHERE id=%s", (
                    fields.Datetime.to_string(future_nextcall.astimezone(pytz.UTC)),
                    bid))
            if job['id'] == cron.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler').id:
                bid = cron.ref('auto_odoo_db_and_file_backup.rule_upload_backup_to_folder').id
                cron_cr.execute("UPDATE database_backup SET next_exec_dt=%s" + " WHERE id=%s", (
                    fields.Datetime.to_string(future_nextcall.astimezone(pytz.UTC)),
                    bid))
            if job['id'] == cron.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_Gdrive').id:
                bid = cron.ref('auto_odoo_db_and_file_backup.rule_upload_backup_to_drive').id
                cron_cr.execute("UPDATE database_backup SET next_exec_dt=%s" + " WHERE id=%s", (
                    fields.Datetime.to_string(future_nextcall.astimezone(pytz.UTC)),
                    bid))
            if job['id'] == cron.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_ftp').id:
                bid = cron.ref('auto_odoo_db_and_file_backup.rule_upload_backup_to_ftp').id
                cron_cr.execute("UPDATE database_backup SET next_exec_dt=%s" + " WHERE id=%s", (
                    fields.Datetime.to_string(future_nextcall.astimezone(pytz.UTC)),
                    bid))
            if job['id'] == cron.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_sftp').id:
                bid = cron.ref('auto_odoo_db_and_file_backup.rule_upload_backup_to_sftp').id
                cron_cr.execute("UPDATE database_backup SET next_exec_dt=%s" + " WHERE id=%s", (
                    fields.Datetime.to_string(future_nextcall.astimezone(pytz.UTC)),
                    bid))
            if job['id'] == cron.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_AWSs3').id:
                bid = cron.ref('auto_odoo_db_and_file_backup.rule_upload_backup_to_AWSs3').id
                cron_cr.execute("UPDATE database_backup SET next_exec_dt=%s" + " WHERE id=%s", (
                    fields.Datetime.to_string(future_nextcall.astimezone(pytz.UTC)),
                    bid))

        cron_cr.execute("""
            DELETE FROM ir_cron_trigger
            WHERE cron_id = %s
              AND call_at < (now() at time zone 'UTC')
        """, [job['id']])

        cron_cr.commit()


class AutoDatabaseBackupStatus(models.Model):
    _name = 'auto.database.backup.status'
    _description = 'Auto Database Backup Status'

    name = fields.Char("Status")
    date = fields.Datetime("Date")


class AutoDatabaseBackup(models.Model):
    _name = 'auto.database.backup'
    _description = 'Auto Database Backup configuration'

    bkup_email = fields.Char("Successful Backup Notification Email")
    bkup_fail_email = fields.Char("Failed Backup Notification Email")
    autoremove = fields.Boolean('Auto. Remove Backups',
                                help='If you check this option you can choose to automatically remove the backup '
                                     'after xx days')
    days_to_keep = fields.Integer('Remove after x days',
                                  help="Choose after how many days the backup should be deleted. For example:\n"
                                       "If you fill in 5 the backups will be removed after 5 days.",
                                  )
    name = fields.Char("Filename")
    bkpu_rules = fields.One2many('database.backup', 'backup_id', "Auto Database Backup Rules")


class DatabaseBackup(models.Model):
    _name = 'database.backup'
    _description = 'Auto Database Backup Rules'

    def _get_abs_file_path(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__))).split('/')
        p1 = path[: len(path) - 3]
        p2 = "/".join(p1)
        dirlist = [(os.path.join(p2, filename), os.path.join(p2, filename)) for filename in os.listdir(p2) if
                   os.path.isdir(os.path.join(p2, filename))]
        return dirlist

    def _get_abs_file_path2(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__))).split('/')
        p1 = path[: len(path) - 3]
        p2 = "/".join(p1)
        dirlist = [(os.path.join(p2, filename), os.path.join(p2, filename)) for filename in os.listdir(p2) if
                   os.path.isdir(os.path.join(p2, filename))]
        return dirlist

        # Columns for local server configuration

    backup_id = fields.Many2one("auto.database.backup", "Auto Backup")
    is_active = fields.Boolean("Active", )
    interval_number = fields.Integer("Interval Number", default=1, )
    interval_type = fields.Selection([('minutes', 'Minutes'),
                                      ('hours', 'Hours'),
                                      ('days', 'Days'),
                                      ('weeks', 'Weeks'),
                                      ('months', 'Months')], string='Interval Unit', default='days')
    backup_type = fields.Selection([('zip', 'Zip'), ('dump', 'Dump')], 'Backup Type', required=True, default='zip')
    backup_destination = fields.Selection([('folder', 'Folder'), ('g_drive', 'Google Drive'),
                                           ('dropbox', 'Dropbox'), ('ftp', 'FTP'), ('sftp', 'SFTP'),
                                           ('AWSs3', 'AWS S3')], 'Backup Destination', readonly=True, default='folder')
    next_exec_dt = fields.Datetime("Next Excecution Date", default=fields.Datetime.now, required=True, )
    backup = fields.Selection([('db_only', 'Database Only'), ('db_and_files', 'Database and Files')], 'Backup',
                              default='db_only')
    files_path = fields.Selection(selection=_get_abs_file_path, string='Files Path',
                                  help="Mention files path for the files, you want to take backup.")
    folder = fields.Selection(selection=_get_abs_file_path2, string='Backup Directory',
                              help='Absolute path for storing the backups')
    foldername = fields.Char("Foldername", help='Foldername for storing the backups', default="Backups")

    # fields for Google Drive uploads
    google_drive_uri = fields.Char(compute='_compute_drive_uri', string='URI',
                                   help="The URL to generate the authorization code from Google")
    google_drive_authorization_code = fields.Char(string='Google Authorization Code')
    google_drive_refresh_token = fields.Text(string='google Drive Refresh Token', )
    google_drive_authorization_code_old = fields.Char(string='Old Google Authorization Code')
    is_cred_avail = fields.Boolean("Credentials Available??", compute="get_is_cred_avail")

    # dropbox fields
    d_app_key = fields.Char("App key")
    d_app_secret = fields.Char("App secret")
    dropbox_uri = fields.Char(string='Dropbox URI', help="The URL to generate the authorization code from Dropbox", )
    dropbox_authorization_code = fields.Char(string='Dropbox Authorization Code')
    dropbox_token = fields.Text(string='Access Token', )
    dropbox_authorization_code_old = fields.Char(string='Old Dropbox Authorization Code')
    dropbox_code_verifier = fields.Char("Dropbox Code Verifier")
    dropbox_refresh_token = fields.Text(string='Dropbox Refresh Token', )
    # FTP fields
    ftp_address = fields.Char('FTP Address',
                              help='The IP address from your remote server. For example 192.168.0.1')
    ftp_port = fields.Integer('FTP Port', help='The port on the FTP server that accepts SSH/SFTP calls.')
    ftp_usrnm = fields.Char('FTP Username',
                            help='The username where the FTP connection should be made with. This is the user on the '
                                 'external server.')
    ftp_pwd = fields.Char('FTP Password',
                          help='The password from the user where the FTP connection should be made with. This '
                               'is the password from the user on the external server.')
    ftp_path = fields.Char('FTP Path',
                           help='The location to the folder where the dumps should be written to. For example '
                                '/odoo/backups/.\nFiles will then be written to /odoo/backups/ on your remote server.')
    # SFTP fields
    sftp_host = fields.Char('SFTP Host',
                            help='The IP address from your remote server. For example 192.168.0.1')
    sftp_user = fields.Char('SFTP User',
                            help='The username where the SFTP connection should be made with. This is the user on the '
                                 'external server.')
    sftp_keyfilepath = fields.Char("SFTP Key File Path(Use .pem File)",
                                   help='Add file path where key file for SFTP connection is present.')
    sftp_file_path = fields.Char('SFTP Path',
                                 help='The location to the folder where the dumps should be written to. For example '
                                      '/odoo/backups/.\nFiles will then be written to /odoo/backups/ on your remote '
                                      'server.')
    upload_file = fields.Binary(string="Upload File")
    file_name = fields.Char(string="File Name")
    is_pem_file_avail = fields.Boolean(".pem File Available??")
    sftp_port = fields.Integer('SFTP Port', help='The port on the FTP server that accepts SSH/SFTP calls.')
    # AWS S3
    s3_app_key_id = fields.Char("AWS S3 app key")
    s3_secret_key_id = fields.Char("AWS S3 secret key")
    s3_bucket_name = fields.Char("Bucket Name")

    def get_gdrive_auth_code(self):
        print()

    @api.onchange('upload_file')
    def onchange_upload_file(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__))).split('/')
        p1 = path[: len(path) - 3]
        p2 = "/".join(p1)
        try:
            path1 = p2 + "/" + self.file_name
            if not os.path.exists(path1):
                with open(path1, 'w') as fp:
                    pass

            File = base64.b64decode(self.upload_file)
            file_string = File.decode('utf-8')
            file1 = open(path1, 'w+')
            file1.write(file_string)
            file1.close()
            self.sftp_keyfilepath = path1
        except Exception as e:
            msg = e
            if "Permission denied" in str(e):
                msg = "Please give write permission to Directory: %s" % (p2,)
            raise UserError(_(msg))

    def change_nextcall_datetime(self, rec):
        unit = rec.interval_number
        now = datetime.datetime.now()
        if rec.interval_type == 'days':
            dd = now + datetime.timedelta(days=unit)
            rec.write({'next_exec_dt': dd})
        elif rec.interval_type == 'weeks':
            wunit = 7 * unit
            wd = now + datetime.timedelta(days=wunit)
            rec.write({'next_exec_dt': wd})
        elif rec.interval_type == 'months':
            md = now + relativedelta(months=+unit)
            rec.write({'next_exec_dt': md})
        elif rec.interval_type == 'hours':
            hd = now + datetime.timedelta(hours=unit)
            rec.write({'next_exec_dt': hd})
        else:
            mind = now + datetime.timedelta(minutes=unit)
            rec.write({'next_exec_dt': mind})

    def write(self, vals):
        result = super(DatabaseBackup, self).write(vals)
        cr = self._cr
        if "is_active" in vals:
            if self.backup_destination == 'folder':
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler')
                ir_cron = self.env['ir.cron'].browse(cron_id.id)
                ir_cron.write({'active': vals.get('is_active')})
            elif self.backup_destination == 'g_drive':
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_Gdrive')
                ir_cron = self.env['ir.cron'].browse(cron_id.id)
                ir_cron.write({'active': vals.get('is_active')})
            elif self.backup_destination == 'dropbox':
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_dropbox')
                ir_cron = self.env['ir.cron'].browse(cron_id.id)
                ir_cron.write({'active': vals.get('is_active')})
            elif self.backup_destination == 'ftp':
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_ftp')
                ir_cron = self.env['ir.cron'].browse(cron_id.id)
                ir_cron.write({'active': vals.get('is_active')})
            elif self.backup_destination == 'sftp':
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_sftp')
                ir_cron = self.env['ir.cron'].browse(cron_id.id)
                ir_cron.write({'active': vals.get('is_active')})
            else:
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_AWSs3')
                ir_cron = self.env['ir.cron'].browse(cron_id.id)
                ir_cron.write({'active': vals.get('is_active')})
        if "interval_number" in vals:
            if self.backup_destination == 'folder':
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler')
                ir_cron = self.env['ir.cron'].browse(cron_id.id)
                ir_cron.write({'interval_number': vals.get('interval_number')})
            elif self.backup_destination == 'g_drive':
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_Gdrive')
                ir_cron = self.env['ir.cron'].browse(cron_id.id)
                ir_cron.write({'interval_number': vals.get('interval_number')})
            elif self.backup_destination == 'dropbox':
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_dropbox')
                ir_cron = self.env['ir.cron'].browse(cron_id.id)
                ir_cron.write({'interval_number': vals.get('interval_number')})
            elif self.backup_destination == 'ftp':
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_ftp')
                ir_cron = self.env['ir.cron'].browse(cron_id.id)
                ir_cron.write({'interval_number': vals.get('interval_number')})
            elif self.backup_destination == 'sftp':
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_sftp')
                ir_cron = self.env['ir.cron'].browse(cron_id.id)
                ir_cron.write({'interval_number': vals.get('interval_number')})
            else:
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_AWSs3')
                ir_cron = self.env['ir.cron'].browse(cron_id.id)
                ir_cron.write({'interval_number': vals.get('interval_number')})
        if "interval_type" in vals:
            if self.backup_destination == 'folder':
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler')
                ir_cron = self.env['ir.cron'].browse(cron_id.id)
                ir_cron.write({'interval_type': vals.get('interval_type')})
            elif self.backup_destination == 'g_drive':
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_Gdrive')
                ir_cron = self.env['ir.cron'].browse(cron_id.id)
                ir_cron.write({'interval_type': vals.get('interval_type')})
            elif self.backup_destination == 'dropbox':
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_dropbox')
                ir_cron = self.env['ir.cron'].browse(cron_id.id)
                ir_cron.write({'interval_type': vals.get('interval_type')})
            elif self.backup_destination == 'ftp':
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_ftp')
                ir_cron = self.env['ir.cron'].browse(cron_id.id)
                ir_cron.write({'interval_type': vals.get('interval_type')})
            elif self.backup_destination == 'sftp':
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_sftp')
                ir_cron = self.env['ir.cron'].browse(cron_id.id)
                ir_cron.write({'interval_type': vals.get('interval_type')})
            else:
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_AWSs3')
                ir_cron = self.env['ir.cron'].browse(cron_id.id)
                ir_cron.write({'interval_type': vals.get('interval_type')})
        if "next_exec_dt" in vals:
            if self.backup_destination == 'folder':
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler')
                cr.execute("UPDATE ir_cron SET nextcall=%s WHERE id=%s", (
                    vals.get('next_exec_dt'),
                    cron_id.id
                ))
            elif self.backup_destination == 'g_drive':
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_Gdrive')
                cr.execute("UPDATE ir_cron SET nextcall=%s WHERE id=%s", (
                    vals.get('next_exec_dt'),
                    cron_id.id
                ))
            elif self.backup_destination == 'dropbox':
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_dropbox')
                cr.execute("UPDATE ir_cron SET nextcall=%s WHERE id=%s", (
                    vals.get('next_exec_dt'),
                    cron_id.id
                ))
            elif self.backup_destination == 'ftp':
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_ftp')
                cr.execute("UPDATE ir_cron SET nextcall=%s WHERE id=%s", (
                    vals.get('next_exec_dt'),
                    cron_id.id
                ))
            elif self.backup_destination == 'sftp':
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_sftp')
                cr.execute("UPDATE ir_cron SET nextcall=%s WHERE id=%s", (
                    vals.get('next_exec_dt'),
                    cron_id.id
                ))
            else:
                cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_AWSs3')
                cr.execute("UPDATE ir_cron SET nextcall=%s WHERE id=%s", (
                    vals.get('next_exec_dt'),
                    cron_id.id
                ))
        return result

    def trigger_direct(self):
        backup_destination = self.env.context.get('backup_destination')
        actid = self.env.context.get('id')
        rec = self.env['database.backup'].browse(actid)
        if backup_destination == 'folder':
            cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler')
            IrCron = self.env['ir.cron'].browse(cron_id.id)
            IrCron.with_user(IrCron.sudo().user_id).ir_actions_server_id.run()
            self.change_nextcall_datetime(rec)
        elif backup_destination == 'g_drive':
            cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_Gdrive')
            IrCron = self.env['ir.cron'].browse(cron_id.id)
            IrCron.with_user(IrCron.sudo().user_id).ir_actions_server_id.run()
            self.change_nextcall_datetime(rec)
        elif backup_destination == 'dropbox':
            cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_dropbox')
            IrCron = self.env['ir.cron'].browse(cron_id.id)
            IrCron.with_user(IrCron.sudo().user_id).ir_actions_server_id.run()
            self.change_nextcall_datetime(rec)
        elif backup_destination == 'ftp':
            cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_ftp')
            IrCron = self.env['ir.cron'].browse(cron_id.id)
            IrCron.with_user(IrCron.sudo().user_id).ir_actions_server_id.run()
            self.change_nextcall_datetime(rec)
        elif backup_destination == 'sftp':
            cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_sftp')
            IrCron = self.env['ir.cron'].browse(cron_id.id)
            IrCron.with_user(IrCron.sudo().user_id).ir_actions_server_id.run()
            self.change_nextcall_datetime(rec)
        else:
            cron_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler_AWSs3')
            IrCron = self.env['ir.cron'].browse(cron_id.id)
            IrCron.with_user(IrCron.sudo().user_id).ir_actions_server_id.run()
            self.change_nextcall_datetime(rec)
        return True

    def test_sftp_connection(self, context=None):
        self.ensure_one()

        # Check if there is a success or fail and write messages
        message_title = ""
        message_content = ""
        error = ""
        has_failed = False

        for rec in self:
            ip_host = rec.sftp_host
            user = rec.sftp_user
            key_path = rec.sftp_keyfilepath

            # Connect with external server over SFTP, so we know sure that everything works.
            if rec.is_pem_file_avail:
                try:
                    cnopts = pysftp.CnOpts()
                    cnopts.hostkeys = None
                    with pysftp.Connection(host=ip_host, username=user,
                                           private_key=key_path, cnopts=cnopts) as sftp:
                        message_title = _(
                            "Connection Test Succeeded!\nEverything seems properly set up for SFTP back-ups!")
                except SSHException as ssh_err:
                    _logger.critical('There was a problem connecting to the remote sftp: ' + str(ssh_err.args[0]))
                    error += str(ssh_err)
                    has_failed = True
                    message_title = _("Connection Test Failed!")
                    message_content += _("Here is what we got instead:\n")
            else:
                password = rec.sftp_keyfilepath
                port_host = rec.sftp_port
                try:
                    s = paramiko.SSHClient()
                    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    s.connect(ip_host, port_host, user, password, timeout=10)
                    sftp = s.open_sftp()
                    message_title = _("Connection Test Succeeded!\nEverything seems properly set up for FTP back-ups!")
                except Exception as e:
                    _logger.critical('There was a problem connecting to the remote sftp: %s', str(e))
                    error += str(e)
                    has_failed = True
                    message_title = _("Connection Test Failed!")
                    if len(rec.sftp_host) < 8:
                        message_content += "\nYour IP address seems to be too short.\n"
                    message_content += _("Here is what we got instead:\n")
                finally:
                    if s:
                        s.close()

        if has_failed:
            raise Warning(message_title + '\n\n' + message_content + "%s" % str(error))
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': message_title,
                    'type': 'success',
                    'sticky': False,
                }
            }

    def test_ftp_connection(self, context=None):
        self.ensure_one()

        # Check if there is a success or fail and write messages
        message_title = ""
        message_content = ""
        error = ""
        has_failed = False

        for rec in self:
            ip_host = rec.ftp_address
            port_host = rec.ftp_port
            username_login = rec.ftp_usrnm
            password_login = rec.ftp_pwd

            # Connect with external server over SFTP, so we know sure that everything works.
            try:
                server = ftplib.FTP()
                server.connect(ip_host, port_host)
                server.login(username_login, password_login)
                message_title = _("Connection Test Succeeded!\nEverything seems properly set up for FTP back-ups!")
            except Exception as e:
                _logger.critical('There was a problem connecting to the remote ftp: ' + str(e))
                error += str(e)
                has_failed = True
                message_title = _("Connection Test Failed!")
                if len(rec.ftp_address) < 8:
                    message_content += "\nYour IP address seems to be too short.\n"
                message_content += _("Here is what we got instead:\n")
            finally:
                if server:
                    server.close()

        if has_failed:
            raise UserError(message_title + '\n\n' + message_content + "%s" % str(error))
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': message_title,
                    'type': 'success',
                    'sticky': False,
                }
            }

    def get_auth_code(self):
        if not self.d_app_key:
            raise UserError(_("App Key is required"))
        auth_flow = DropboxOAuth2FlowNoRedirect(self.d_app_key, use_pkce=True, token_access_type='offline')
        authorize_url = "https://www.dropbox.com/oauth2/authorize?response_type=code&client_id=%s&token_access_type=offline&code_challenge=%s&code_challenge_method=S256" % (
            self.d_app_key, auth_flow.code_challenge,)
        self.write({'dropbox_code_verifier': auth_flow.code_verifier, 'dropbox_uri': authorize_url})
        ctx = {'default_dropbox_uri': authorize_url, 'backup_id': self.id}
        return {
            'view_mode': 'form',
            'res_model': 'dropbox.auth.refresh.token.wiz',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': ctx,
            'target': 'new',
        }

    def get_auth_refresh_token(self):
        conn = http.client.HTTPSConnection("api.dropbox.com")
        payload = "grant_type=authorization_code&client_id=%s&code_verifier=%s&code=%s" % (
            self.d_app_key, self.dropbox_code_verifier, self.dropbox_authorization_code,)
        headers = {'Accept': "application/json", 'content-type': "application/x-www-form-urlencoded"}
        conn.request("POST", "/oauth2/token", payload, headers)
        res = conn.getresponse()
        data = res.read()
        data = json.loads(data.decode("utf-8"))
        self.dropbox_refresh_token = data.get('refresh_token')

    @api.onchange('google_drive_authorization_code')
    def _action_setup_token(self):
        for rec in self:
            if rec.google_drive_authorization_code:
                if not rec.google_drive_refresh_token:
                    authorization_code = rec.google_drive_authorization_code
                    refresh_token = (
                        self.env['google.service'].generate_refresh_token('drive', authorization_code)
                        if authorization_code else False
                    )
                    self.write({'google_drive_authorization_code_old': authorization_code, })
                    rec.google_drive_refresh_token = refresh_token
                else:
                    if rec.google_drive_authorization_code != rec.google_drive_authorization_code_old:
                        authorization_code = rec.google_drive_authorization_code
                        refresh_token = (
                            self.env['google.service'].generate_refresh_token('drive', authorization_code)
                            if authorization_code else False
                        )
                        self.write({'google_drive_authorization_code_old': authorization_code, })
                        rec.google_drive_refresh_token = refresh_token
                    else:
                        rec.google_drive_refresh_token = rec.google_drive_refresh_token
            else:
                rec.google_drive_refresh_token = rec.google_drive_refresh_token

    @api.onchange('dropbox_authorization_code', 'd_app_key', 'd_app_secret')
    def action_setup_dropbox_token(self):
        for rec in self:
            if rec.d_app_key and rec.d_app_secret and rec.dropbox_authorization_code:
                if not rec.dropbox_token:
                    try:
                        token_url = "https://api.dropbox.com/oauth2/token"
                        params = {
                            "code": rec.dropbox_authorization_code,
                            "grant_type": "authorization_code",
                            "client_id": rec.d_app_key,
                            "client_secret": rec.d_app_secret
                        }
                        r = requests.post(token_url, data=params)
                        response = json.loads(r.text)
                        self.write({'dropbox_authorization_code_old': rec.dropbox_authorization_code})
                        rec.dropbox_token = response.get('access_token')
                    except Exception as e:
                        _logger.debug(e)
                        exit(1)
                        raise Warning(e)
                else:
                    if rec.dropbox_authorization_code != rec.dropbox_authorization_code_old:
                        try:
                            token_url = "https://api.dropbox.com/oauth2/token"
                            params = {
                                "code": rec.dropbox_authorization_code,
                                "grant_type": "authorization_code",
                                "client_id": rec.d_app_key,
                                "client_secret": rec.d_app_secret
                            }
                            r = requests.post(token_url, data=params)
                            response = json.loads(r.text)
                            self.write({'dropbox_authorization_code_old': rec.dropbox_authorization_code})
                            self.dropbox_token = response.get('access_token')
                        except Exception as e:
                            _logger.debug(e)
                            exit(1)
                            raise Warning(e)
                    else:
                        rec.dropbox_token = rec.dropbox_token
            else:
                rec.dropbox_token = rec.dropbox_token

    @api.depends('google_drive_authorization_code')
    def _compute_drive_uri(self):
        google_drive_uri = ""  # self.env['google.service']._get_google_token_uri('drive', scope=self.env['google.drive.config'].get_google_scope())
        for config in self:
            config.google_drive_uri = "https://console.cloud.google.com/apis"

    def send_success_mail_notificaton(self, rec, bkp_file, bkp_folder):
        email_to = rec.backup_id.bkup_email
        BackupType = dict(self._fields['backup_type'].selection)
        BackupDest = dict(self._fields['backup_destination'].selection)
        if rec.backup_destination == 'folder':
            notification_template = self.env.ref('auto_odoo_db_and_file_backup.email_local_upload')
            folder = rec.folder
            if rec.folder.endswith('/'):
                folder = rec.folder.strip('/')
            submsg1 = folder + "/" + rec.foldername
            submsg2 = ""
            subject = "Folder Upload Successful"
        if rec.backup_destination == 'g_drive':
            notification_template = self.env.ref('auto_odoo_db_and_file_backup.email_google_drive_upload')

            submsg1 = "<a href='https://drive.google.com/drive/my-drive'>https://drive.google.com/drive/my-drive</a>"
            submsg2 = ""
            subject = "Google Drive Upload Successful"
        if rec.backup_destination == 'dropbox':
            notification_template = self.env.ref('auto_odoo_db_and_file_backup.email_dropbox_upload')
            submsg1 = "<a href='https://www.dropbox.com/home?preview=%s'>https://www.dropbox.com/home?preview=%s</a>" % (
                bkp_file, bkp_file)
            submsg2 = "<a href='https://www.dropbox.com/home?preview=%s'>https://www.dropbox.com/home?preview=%s</a>" % (
                bkp_folder, bkp_folder)
            subject = "Dropbox Upload Successful"
        if rec.backup_destination == 'ftp':
            notification_template = self.env.ref('auto_odoo_db_and_file_backup.email_ftp_upload')
            submsg1 = rec.ftp_path
            submsg2 = ""
            subject = "FTP Upload Successful"
        if rec.backup_destination == 'sftp':
            notification_template = self.env.ref('auto_odoo_db_and_file_backup.email_sftp_upload')
            submsg1 = rec.sftp_file_path
            submsg2 = ""
            subject = "SFTP Upload Successful"

        if rec.backup_destination == 'AWSs3':
            notification_template = self.env.ref('auto_odoo_db_and_file_backup.email_AWSs3_upload')
            submsg1 = "In Bucket " + rec.s3_bucket_name
            submsg2 = ""
            subject = "AWS S3 Upload Successful"

        if rec.backup == 'db_only':
            msg = "<h3>Backup Successfully Created!</h3>" \
                  "Please see below details. <br/> <br/> " \
                  "<p>Backup : Database Only </p>" \
                  "<p>Backup Type : %s" % (str(BackupType.get(rec.backup_type))) + "</p>" \
                                                                                   "<p>Backup Destination : %s" % (
                      str(BackupDest.get(rec.backup_destination))) + "</p>" \
                                                                     "<p>Backup Directory : %s" % (
                      str(submsg1)) + "</p>" \
                                      "<p>Filename : %s" % (str(bkp_file)) + "</p>"
        else:
            msg = "<h3>Backup Successfully Created!</h3>" \
                  "Please see below details. <br/> <br/> " \
                  "<p>Backup : Database and Files</p>" \
                  "<p>Backup Type : %s" % (str(BackupType.get(rec.backup_type))) + "</p>" \
                                                                                   "<p>Backup Destination : %s" % (
                      str(BackupDest.get(rec.backup_destination))) + "</p>" \
                                                                     "<p>Backup Directory : %s" % (
                      str(submsg1)) + "<br/>" + (str(submsg2)) + "</p>" \
                                                                 "<p>DB Filename : %s" % (str(bkp_file)) + "</p>" \
                                                                                                           "<p>Files : %s" % (
                      str(bkp_folder)) + "</p>"
        email_values = {
            'email_from': self.env['res.users'].browse(self.env.uid).company_id.email,
            'email_to': email_to, 'subject': subject, 'body_html': msg,
        }
        notification_template.send_mail(rec.id, force_send=True, email_values=email_values)

    def send_fail_mail_notificaton(self, rec, bkp_file, bkp_folder, error):
        email_to = rec.backup_id.bkup_fail_email

        if rec.backup_destination == 'folder':
            notification_template = self.env.ref('auto_odoo_db_and_file_backup.email_local_upload')
            subject = "Folder Upload Failed"
        if rec.backup_destination == 'g_drive':
            notification_template = self.env.ref('auto_odoo_db_and_file_backup.email_google_drive_upload')
            subject = "Google Drive Upload Failed"
        if rec.backup_destination == 'dropbox':
            notification_template = self.env.ref('auto_odoo_db_and_file_backup.email_dropbox_upload')
            subject = "Dropbox Upload Failed"
        if rec.backup_destination == 'ftp':
            notification_template = self.env.ref('auto_odoo_db_and_file_backup.email_ftp_upload')
            subject = "FTP Upload Failed"
        if rec.backup_destination == 'sftp':
            notification_template = self.env.ref('auto_odoo_db_and_file_backup.email_sftp_upload')
            subject = "SFTP Upload Failed"
        if rec.backup_destination == 'AWSs3':
            notification_template = self.env.ref('auto_odoo_db_and_file_backup.email_AWSs3_upload')
            subject = "AWS S3 Upload Failed"

        if rec.backup == 'db_only':
            msg = "<h3>Backup Upload Failed!</h3>" \
                  "Please see below details. <br/> <br/> " \
                  "<table style='width:100%'>" \
                  "<tr> " \
                  "<th align='left'>Backup</th>" \
                  "<td>" + (str(bkp_file)) + "</td></tr>" \
                                             "<tr> " \
                                             "<th align='left'>Error: </th>" \
                                             "<td>" + str(error) + "</td>" \
                                                                   "</tr>" \
                                                                   "</table>"
        else:
            msg = "<h3>Backup Upload Failed!</h3>" \
                  "Please see below details. <br/> <br/> " \
                  "<table style='width:100%'>" \
                  "<tr> " \
                  "<th align='left'>Backup</th>" \
                  "<td>" + (str(bkp_file)) + (str(bkp_folder)) + "</td></tr>" \
                                                                 "<tr> " \
                                                                 "<th align='left'>Error: </th>" \
                                                                 "<td>" + str(error) + "</td>" \
                                                                                       "</tr>" \
                                                                                       "</table>"
        email_values = {
            'email_from': self.env['res.users'].browse(self.env.uid).company_id.email,
            'email_to': email_to, 'subject': subject, 'body_html': msg,
        }
        notification_template.send_mail(rec.id, force_send=True, email_values=email_values)

    @api.model
    def schedule_auto_db_backup(self):
        conf_id = self.search([('is_active', '=', True), ('backup_destination', '=', 'folder')])
        if conf_id:
            user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz)
            date_today = pytz.utc.localize(datetime.datetime.today()).astimezone(user_tz)
            try:
                StatusObj = self.env['auto.database.backup.status']
                folder = conf_id.folder
                if conf_id.folder.endswith('/'):
                    folder = conf_id.folder.strip('/')
                Folder_Path = folder + "/" + conf_id.foldername
                if not os.path.isdir(Folder_Path):
                    os.makedirs(Folder_Path)
                # Create name for dumpfile.
                bkp_file = '%s_%s.%s' % (
                    self.env.cr.dbname, date_today.strftime('%Y-%m-%d_%H_%M_%S'), conf_id.backup_type)
                file_path = os.path.join(Folder_Path, bkp_file)
                bkp_folder = ""
                # try to backup database and write it away
                fp = open(file_path, 'wb')
                conf_id._take_dump(self.env.cr.dbname, fp, 'database.backup', conf_id.backup_destination,
                                   conf_id.backup_type)
                fp.close()
                if conf_id.backup == 'db_and_files':
                    fpath = conf_id.files_path.split('/')[-1]
                    bkp_folder = '%s_%s.%s' % (fpath, date_today.strftime('%Y-%m-%d_%H_%M_%S'), "zip")
                    bkp_folder_path = os.path.join(Folder_Path, bkp_folder)
                    with tempfile.TemporaryDirectory() as dump_dirf:
                        if os.path.exists(conf_id.files_path):
                            shutil.copytree(conf_id.files_path, os.path.join(dump_dirf, fpath))

                        odoo.tools.osutil.zip_dir(dump_dirf, bkp_folder_path, include_dir=False, fnct_sort=None)

                _logger.info("Backup Successfully Uploaded to Local.")
                StatusObj.create({'date': datetime.datetime.today(), 'name': "Local: Success"})
                if conf_id.backup_id.bkup_email:
                    conf_id.send_success_mail_notificaton(conf_id, bkp_file, bkp_folder)

            except Exception as error:
                _logger.debug(
                    "Couldn't backup database %s. Bad database administrator password for server running at "
                    % (self.env.cr.dbname,))
                _logger.debug("Exact error from the exception: " + str(error))
                StatusObj.create({'date': datetime.datetime.today(), 'name': "Failed (Error: %s)" % (str(error))})
                if conf_id.backup_id.bkup_fail_email:
                    conf_id.send_fail_mail_notificaton(conf_id, bkp_file, bkp_folder, error)
            """
            Remove all old files (on local server) in case this is configured..
            """
            if conf_id.backup_id.autoremove:

                directory = Folder_Path
                # Loop over all files in the directory.
                for f in os.listdir(directory):
                    fullpath = os.path.join(directory, f)
                    # Only delete the ones which are from the current database
                    # (Makes it possible to save different databases in the same folder)
                    if self.env.cr.dbname in fullpath:
                        timestamp = os.path.getmtime(os.path.join(directory, f))
                        createtime = datetime.datetime.fromtimestamp(timestamp)
                        now = datetime.datetime.now()
                        delta = now.date() - createtime.date()
                        if delta.days >= conf_id.backup_id.days_to_keep:
                            # Only delete files (which are .dump and .zip), no directories.
                            if os.path.isfile(fullpath) and (".dump" in f or '.zip' in f):
                                _logger.info("Delete local out-of-date file: " + fullpath)
                                os.remove(fullpath)
                    if conf_id.backup == "db_and_files":
                        fpath = conf_id.files_path.split('/')[-1]
                        if fpath in fullpath:
                            timestamp = os.path.getmtime(os.path.join(directory, f))
                            createtime = datetime.datetime.fromtimestamp(timestamp)
                            now = datetime.datetime.now()
                            delta = now.date() - createtime.date()
                            if delta.days >= conf_id.backup_id.days_to_keep:
                                if os.path.isfile(fullpath) and ('.zip' in f):
                                    _logger.info("Delete local out-of-date file: " + fullpath)
                                    os.remove(fullpath)

    def get_content_files(self, rec):
        err = ""
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz)
        date_today = pytz.utc.localize(datetime.datetime.today()).astimezone(user_tz)
        try:
            # Create name for dumpfile.
            bkp_file = '%s_%s.%s' % (self.env.cr.dbname, date_today.strftime('%Y-%m-%d_%H_%M_%S'), rec.backup_type)

            fd, patht = tempfile.mkstemp(bkp_file)  # can use anything
            try:
                rec._take_dump(self.env.cr.dbname, patht, 'database.backup', rec.backup_destination, rec.backup_type)
            except Exception as E:
                print("Error: ", E)

            with open(patht, 'rb') as db_document:
                db_content = db_document.read()
            dbfile_content = ""
            bkp_folder = ""
            bkp_folder_path = ""
            if rec.backup == 'db_and_files':
                fpath = rec.files_path.split('/')[-1]
                bkp_folder = '%s_%s.%s' % (fpath, date_today.strftime('%Y-%m-%d_%H_%M_%S'), "zip")
                dump_dirf = tempfile.mkdtemp()
                bkp_folder_path = os.path.join(dump_dirf, bkp_folder)
                if os.path.exists(rec.files_path):
                    shutil.copytree(rec.files_path, os.path.join(dump_dirf, fpath))

                odoo.tools.osutil.zip_dir(dump_dirf, bkp_folder_path, include_dir=False, fnct_sort=None)
                with open(bkp_folder_path, 'rb') as dbfile_document:
                    dbfile_content = dbfile_document.read()
            return bkp_file, patht, bkp_folder, bkp_folder_path, err, datetime.datetime.today(), db_content, dbfile_content
        except Exception as error:
            _logger.debug(
                "Couldn't backup database %s. Bad database administrator password for server running" % (
                    self.env.cr.dbname,))
            _logger.debug("Exact error from the exception: " + str(error))
            return "", "", "", "", error, datetime.datetime.today(), "", ""

    @api.model
    def schedule_auto_db_backup_to_Gdrive(self):
        conf_id = self.search([('is_active', '=', True), ('backup_destination', '=', 'g_drive')])
        if conf_id:
            cred_fp = os.path.join(os.path.dirname(os.path.abspath(__file__))) + "/client_secrets.json"
            if not os.path.exists(cred_fp):
                raise UserError(
                    _("client_secrets.json does not exist. First add credentials file in path auto_odoo_db_and_file_backup/models."))

            StatusObj = self.env['auto.database.backup.status']
            bkp_file, file_path2, bkp_folder, bkp_folder_path, err, date_today, db_content, dbfile_content = conf_id.get_content_files(
                conf_id)
            if err == "":
                status = 1
                conf_id.google_drive_upload(conf_id, file_path2, bkp_file, bkp_file, bkp_folder, status, date_today,
                                            db_content, dbfile_content)
                status = 2
                time.sleep(3)
                if conf_id.backup == 'db_and_files':
                    conf_id.google_drive_upload(conf_id, bkp_folder_path, bkp_folder, bkp_file, bkp_folder, status,
                                                date_today, db_content, dbfile_content)
            else:
                StatusObj.create({'date': date_today, 'name': "Failed (Error: %s)" % (str(err))})

    @api.model
    def schedule_auto_db_backup_to_dropbox(self):
        conf_id = self.search([('is_active', '=', True), ('backup_destination', '=', 'dropbox')])
        if conf_id:
            StatusObj = self.env['auto.database.backup.status']
            bkp_file, file_path2, bkp_folder, bkp_folder_path, err, date_today, db_content, dbfile_content = conf_id.get_content_files(
                conf_id)
            if err == "":
                status = 1
                conf_id.dropbox_upload(conf_id, file_path2, bkp_file, bkp_file, bkp_folder, status, date_today,
                                       db_content, dbfile_content)
                time.sleep(3)
                status = 2
                if conf_id.backup == 'db_and_files':
                    conf_id.dropbox_upload(conf_id, bkp_folder_path, bkp_folder, bkp_file, bkp_folder, status,
                                           date_today, db_content, dbfile_content)
            else:
                StatusObj.create({'date': date_today, 'name': "Failed (Error: %s)" % (str(err))})

    @api.model
    def schedule_auto_db_backup_to_ftp(self):
        conf_id = self.search([('is_active', '=', True), ('backup_destination', '=', 'ftp')])
        if conf_id:
            bkp_file, file_path2, bkp_folder, bkp_folder_path, err, date_today, db_content, dbfile_content = conf_id.get_content_files(
                conf_id)
            conf_id.ftp_upload(conf_id, file_path2, bkp_file, bkp_folder_path, bkp_folder, err, date_today, db_content,
                               dbfile_content)

    @api.model
    def schedule_auto_db_backup_to_sftp(self):
        conf_id = self.search([('is_active', '=', True), ('backup_destination', '=', 'sftp')])
        if conf_id:
            bkp_file, file_path2, bkp_folder, bkp_folder_path, err, date_today, db_content, dbfile_content = conf_id.get_content_files(
                conf_id)
            conf_id.sftp_upload(conf_id, file_path2, bkp_file, bkp_folder_path, bkp_folder, err, date_today, db_content,
                                dbfile_content)

    @api.model
    def schedule_auto_db_backup_to_AWSs3(self):
        conf_id = self.search([('is_active', '=', True), ('backup_destination', '=', 'AWSs3')])
        if conf_id:
            bkp_file, file_path2, bkp_folder, bkp_folder_path, err, date_today, db_content, dbfile_content = conf_id.get_content_files(
                conf_id)
            conf_id.AWSs3_upload(conf_id, file_path2, bkp_file, bkp_folder_path, bkp_folder, err, date_today,
                                 db_content, dbfile_content)

    def get_datetime_format(self, date_time):
        # convert to datetime object
        date_time = datetime.datetime.strptime(date_time, "%Y%m%d%H%M%S").date()
        # convert to human readable date time string
        strdt = date_time.strftime("%Y-%m-%d")
        return datetime.datetime.strptime(strdt, "%Y-%m-%d").date()

    def sftp_upload(self, rec, file_path, bkp_file, bkp_folder_path, bkp_folder, err, date_today, db_content,
                    dbfile_content):
        StatusObj = self.env['auto.database.backup.status']
        if err == "":
            try:
                if rec.is_pem_file_avail:
                    cnopts = pysftp.CnOpts()
                    cnopts.hostkeys = None
                    with pysftp.Connection(host=rec.sftp_host, username=rec.sftp_user,
                                           private_key=rec.sftp_keyfilepath, cnopts=cnopts) as sftp:
                        remote = rec.sftp_file_path
                        if remote.endswith('/'):
                            remote = remote.strip('/')
                        remoteFilePath = remote + "/" + bkp_file
                        sftp.put(file_path, remoteFilePath)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        if rec.backup == 'db_and_files':
                            remoteFilePath2 = remote + "/" + bkp_folder
                            sftp.put(bkp_folder_path, remoteFilePath2)
                            if os.path.exists(bkp_folder_path):
                                os.remove(bkp_folder_path)
                        _logger.info("Backup Successfully Uploaded to SFTP.")
                        StatusObj.create({'date': date_today, 'name': "SFTP: Success"})
                        if rec.backup_id.bkup_email:
                            self.send_success_mail_notificaton(rec, bkp_file, bkp_folder)
                        # remove files after x days if auto remove is true
                        if rec.backup_id.autoremove:
                            for entry in sftp.listdir_attr(remote):
                                timestamp = entry.st_mtime
                                createtime = datetime.datetime.fromtimestamp(timestamp).date()
                                date_today1 = datetime.datetime.today().date()
                                delta = date_today1 - createtime
                                if delta.days >= rec.backup_id.days_to_keep:
                                    if entry.filename.endswith(".zip") or entry.filename.endswith(".dump"):
                                        filepath = remote + '/' + entry.filename
                                        if self.env.cr.dbname in entry.filename:
                                            sftp.remove(filepath)
                                        if entry.filename.endswith(".zip") and rec.backup == 'db_and_files':
                                            fpath = rec.files_path.split('/')[-1]
                                            if fpath in entry.filename:
                                                sftp.remove(filepath)
                                        _logger.info("Delete SFTP out-of-date file.")
                else:
                    try:
                        s = paramiko.SSHClient()
                        s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        s.connect(rec.sftp_host, rec.sftp_port, rec.sftp_user, rec.sftp_keyfilepath, timeout=10)
                        sftp = s.open_sftp()
                        remote = rec.sftp_file_path
                        if remote.endswith('/'):
                            remote = remote.strip('/')
                        remoteFilePath = remote + "/" + bkp_file
                        sftp.put(file_path, remoteFilePath)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        if rec.backup == 'db_and_files':
                            remoteFilePath2 = remote + "/" + bkp_folder
                            sftp.put(bkp_folder_path, remoteFilePath2)
                            if os.path.exists(bkp_folder_path):
                                os.remove(bkp_folder_path)
                        _logger.info("Backup Successfully Uploaded to SFTP.")
                        StatusObj.create({'date': date_today, 'name': "SFTP Success"})
                        if rec.backup_id.bkup_email:
                            self.send_success_mail_notificaton(rec, bkp_file, bkp_folder)
                        # remove files after x days if auto remove is true
                        if rec.backup_id.autoremove:
                            for entry in sftp.listdir_attr(remote):
                                timestamp = entry.st_mtime
                                createtime = datetime.datetime.fromtimestamp(timestamp).date()
                                date_today1 = datetime.datetime.today().date()
                                delta = date_today1 - createtime
                                if delta.days >= rec.backup_id.days_to_keep:
                                    if entry.filename.endswith(".zip") or entry.filename.endswith(".dump"):
                                        filepath = remote + '/' + entry.filename
                                        if self.env.cr.dbname in entry.filename:
                                            sftp.remove(filepath)
                                        if entry.filename.endswith(".zip") and rec.backup == 'db_and_files':
                                            fpath = rec.files_path.split('/')[-1]
                                            if fpath in entry.filename:
                                                sftp.remove(filepath)
                                        _logger.info("Delete SFTP out-of-date file.")
                        sftp.close()
                    except Exception as e:
                        _logger.critical('Error in SFTP : %s', str(e))
                        StatusObj.create({'date': date_today, 'name': "Failed (Error: %s)" % (str(e))})
                    finally:
                        if s:
                            s.close()
            except Exception as err:
                _logger.debug("ERROR: %s" % (err,))
                StatusObj.create({'date': date_today, 'name': "Failed (Error: %s)" % (str(err))})
                if rec.backup_id.bkup_fail_email:
                    self.send_fail_mail_notificaton(rec, bkp_file, bkp_folder, err)
        else:
            StatusObj.create({'date': date_today, 'name': "Failed (Error: %s)" % (str(err))})

    def AWSs3_upload(self, rec, file_path, bkp_file, bkp_folder_path, bkp_folder, err, date_today, db_content,
                     dbfile_content):
        StatusObj = self.env['auto.database.backup.status']
        if err == "":
            try:
                s3_app_key_id = rec.s3_app_key_id
                s3_secret_key_id = rec.s3_secret_key_id
                client = boto3.client(
                    's3',
                    aws_access_key_id=s3_app_key_id,
                    aws_secret_access_key=s3_secret_key_id
                )
                try:
                    fp = open(file_path, 'rb')
                    client.upload_fileobj(
                        fp, rec.s3_bucket_name, bkp_file)
                    fp.close()
                except ClientError as e:
                    _logger.debug("ERROR: %s" % (str(e),))
                    StatusObj.create({'date': date_today, 'name': "Failed (Error: %s)" % (str(e))})
                    if rec.backup_id.bkup_fail_email:
                        self.send_fail_mail_notificaton(rec, bkp_file, bkp_folder, e)
                if os.path.exists(file_path):
                    os.remove(file_path)
                if rec.backup == 'db_and_files':
                    try:
                        fp1 = open(bkp_folder_path, 'rb')
                        client.upload_fileobj(
                            fp1, rec.s3_bucket_name, bkp_folder)
                        fp1.close()
                    except ClientError as e:
                        _logger.debug("ERROR: %s" % (str(e),))
                        StatusObj.create({'date': date_today, 'name': "Failed (Error: %s)" % (str(e))})
                        if rec.backup_id.bkup_fail_email:
                            self.send_fail_mail_notificaton(rec, bkp_file, bkp_folder, e)
                    if os.path.exists(bkp_folder_path):
                        os.remove(bkp_folder_path)
                _logger.info("Backup Successfully Uploaded to AWS S3.")
                StatusObj.create({'date': date_today, 'name': "AWS S3: Success"})
                if rec.backup_id.bkup_email:
                    self.send_success_mail_notificaton(rec, bkp_file, bkp_folder)
                # remove files after x days if auto remove is true
                if rec.backup_id.autoremove:
                    utc = pytz.UTC
                    response = client.list_objects_v2(Bucket=rec.s3_bucket_name)
                    KeystoDelete = []
                    for object in response['Contents']:
                        if self.env.cr.dbname in object['Key']:
                            createtime = object['LastModified'].replace(tzinfo=utc).date()
                            date_today1 = datetime.datetime.today().date()
                            delta = date_today1 - createtime
                            if delta.days >= rec.backup_id.days_to_keep:
                                KeystoDelete.append({
                                    'Key': object['Key']
                                })

                    if KeystoDelete:
                        client.delete_objects(Bucket=rec.s3_bucket_name, Delete={
                            'Objects': KeystoDelete})
                    if rec.backup == 'db_and_files':
                        fpath = rec.files_path.split('/')[-1]
                        KeystoDelete1 = []
                        for object1 in response['Contents']:
                            if fpath in object1['Key']:
                                createtime1 = object1['LastModified'].replace(tzinfo=utc).date()
                                date_today2 = datetime.datetime.today().date()
                                delta1 = date_today2 - createtime1
                                if delta1.days >= rec.backup_id.days_to_keep:
                                    KeystoDelete1.append({
                                        'Key': object1['Key']
                                    })

                        if KeystoDelete1:
                            client.delete_objects(Bucket=rec.s3_bucket_name, Delete={
                                'Objects': KeystoDelete1})

                    _logger.info("Delete AWS S3 out-of-date file.")

            except Exception as err:
                _logger.debug("ERROR: %s" % (err,))
                StatusObj.create({'date': date_today, 'name': "Failed (Error: %s)" % (str(err))})
                if rec.backup_id.bkup_fail_email:
                    self.send_fail_mail_notificaton(rec, bkp_file, bkp_folder, err)
        else:
            StatusObj.create({'date': date_today, 'name': "Failed (Error: %s)" % (str(err))})

    def ftp_upload(self, rec, file_path, bkp_file, bkp_folder_path, bkp_folder, err, date_today, db_content,
                   dbfile_content):
        StatusObj = self.env['auto.database.backup.status']
        if err == "":
            try:
                filename = bkp_file
                ftp = ftplib.FTP(rec.ftp_address, timeout=300)
                ftp.login(rec.ftp_usrnm, rec.ftp_pwd)
                ftp.encoding = "utf-8"
                ftp.cwd(rec.ftp_path)
                os.chdir("/tmp")
                buf = io.BytesIO(db_content)
                buf.seek(0)
                ftp.storbinary('STOR ' + filename, buf)
                if os.path.exists(file_path):
                    os.remove(file_path)
                if rec.backup == 'db_and_files':
                    buf1 = io.BytesIO(dbfile_content)
                    buf1.seek(0)
                    ftp.storbinary('STOR ' + bkp_folder, buf1)

                _logger.info("Backup Successfully Uploaded to FTP.")
                StatusObj.create({'date': date_today, 'name': "FTP: Success"})
                if rec.backup == 'db_and_files':
                    if os.path.exists(bkp_folder_path):
                        os.remove(bkp_folder_path)

                if rec.backup_id.bkup_email:
                    self.send_success_mail_notificaton(rec, bkp_file, bkp_folder)
                # remove files after x days if auto remove is true
                if rec.backup_id.autoremove:
                    for file_data in ftp.mlsd():
                        file_name, meta = file_data
                        create_date = self.get_datetime_format(meta.get("modify"))
                        date_today1 = datetime.datetime.today().date()
                        delta1 = date_today1 - create_date
                        if delta1.days >= rec.backup_id.days_to_keep:
                            if file_name.endswith(".zip") or file_name.endswith(".dump"):
                                if self.env.cr.dbname in file_name:
                                    ftp.delete(file_name)
                                if file_name.endswith(".zip") and rec.backup == 'db_and_files':
                                    fpath = rec.files_path.split('/')[-1]
                                    if fpath in file_name:
                                        ftp.delete(file_name)
                                _logger.info("Delete FTP out-of-date file.")
                ftp.quit()
            except Exception as err:
                _logger.debug("ERROR: %s" % (err,))
                StatusObj.create({'date': date_today, 'name': "Failed (Error: %s)" % (str(err))})
                if rec.backup_id.bkup_fail_email:
                    self.send_fail_mail_notificaton(rec, bkp_file, bkp_folder, err)
        else:
            StatusObj.create({'date': date_today, 'name': "Failed (Error: %s)" % (str(err))})

    def dropbox_upload(self, rec, file_path, bkp_file, bkp_file2, bkp_folder, status, date_today, db_content,
                       dbfile_content):
        StatusObj = self.env['auto.database.backup.status']
        #         if rec.dropbox_token:
        if rec.dropbox_refresh_token:
            #             TOKEN = rec.dropbox_token #old
            TOKEN = rec.dropbox_refresh_token
            # Check for an access token
            if (len(TOKEN) == 0):
                _logger.debug(
                    "ERROR: Looks like you didn't add your access token. Please request again an authorization code.")

            # Create an instance of a Dropbox class, which can make requests to the API.
            #             dbx = dropbox.Dropbox(TOKEN,timeout=900) #old
            with dropbox.Dropbox(oauth2_refresh_token=TOKEN, app_key=rec.d_app_key) as dbx:
                # Check that the access token is valid
                try:
                    dbx.users_get_current_account()
                except AuthError as err:
                    _logger.debug("ERROR: %s" % (err,))

                # Create a backup of the current settings file
                with open(file_path, 'rb') as f:
                    # We use WriteMode=overwrite to make sure that the settings in the file
                    # are changed on upload
                    try:
                        dbx.files_upload(f.read(), "/" + bkp_file, mode=WriteMode('overwrite'))
                        _logger.info("Backup Successfully Uploaded to Dropbox.")
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        if rec.backup == 'db_only' and status == 1:
                            StatusObj.create({'date': date_today, 'name': "Dropbox: Success"})
                        if rec.backup == 'db_and_files' and status == 2:
                            StatusObj.create({'date': date_today, 'name': "Success"})
                        if rec.backup_id.bkup_email:
                            if rec.backup == 'db_only' and status == 1:
                                self.send_success_mail_notificaton(rec, bkp_file, bkp_folder)
                            if rec.backup == 'db_and_files' and status == 2:
                                self.send_success_mail_notificaton(rec, bkp_file2, bkp_folder)

                    except ApiError as err:
                        # This checks for the specific error where a user doesn't have enough Dropbox space quota to upload this file
                        if (err.error.is_path() and
                                err.error.get_path().error.is_insufficient_space()):
                            _logger.debug("ERROR: Cannot back up; insufficient space.")
                        elif err.user_message_text:
                            _logger.debug("ERROR: %s" % (err.user_message_text,))
                            sys.exit()
                        else:
                            _logger.debug("ERROR: %s" % (err,))
                            sys.exit()
                        StatusObj.create({'date': date_today, 'name': "Failed (Error: %s)" % (str(err))})
                        if rec.backup_id.bkup_fail_email:
                            self.send_fail_mail_notificaton(rec, bkp_file2, bkp_folder, err)

                # remove files after x days if auto remove is true
                if rec.backup_id.autoremove:
                    for entry in dbx.files_list_folder('').entries:
                        if entry.path_lower.endswith(".zip") or entry.path_lower.endswith(".dump"):
                            date_today1 = datetime.datetime.today().date()
                            create_date = entry.client_modified.date()
                            delta1 = date_today1 - create_date
                            if delta1.days >= rec.backup_id.days_to_keep:
                                if self.env.cr.dbname in entry.name:
                                    dbx.files_delete(entry.path_lower)
                                if entry.path_lower.endswith(".zip") and rec.backup == 'db_and_files':
                                    fpath = rec.files_path.split('/')[-1]
                                    if fpath in entry.name:
                                        dbx.files_delete(entry.path_lower)
                                _logger.info("Delete Dropbox out-of-date file.")

        else:
            _logger.debug(
                "Something went wrong during the token generation. Please request again an authorization code .")

    def get_is_cred_avail(self):
        cred_fp = os.path.join(os.path.dirname(os.path.abspath(__file__))) + "/client_secrets.json"
        for rec in self:
            if os.path.exists(cred_fp):
                rec.is_cred_avail = True
            else:
                rec.is_cred_avail = False

    def get_gdrive_credentials(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_url',
                'url': rec.google_drive_uri,
                'target': 'new',
            }

    def authenticate_gdrive(self):
        for rec in self:
            if not rec.is_cred_avail:
                raise UserError(
                    _("client_secrets.json does not exist. First generate & add credentials file in path auto_odoo_db_and_file_backup/models."))
            try:
                drive = rec.authorize_drive()
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': "Google drive authorized successfully!",
                        'type': 'success',
                        'sticky': False,
                    }
                }
            except Exception as e:
                raise UserError(_(str(e)))

    def authorize_drive(self):
        gauth = GoogleAuth()
        cred_fp = os.path.join(os.path.dirname(os.path.abspath(__file__))) + "/client_secrets.json"
        gauth.DEFAULT_SETTINGS['client_config_file'] = cred_fp
        # Try to load saved client credentials
        gauth.LoadCredentialsFile("mycreds.txt")
        if gauth.credentials is None:
            # Authenticate if they're not there        
            # This is what solved the issues:
            gauth.GetFlow()
            gauth.flow.params.update({'access_type': 'offline'})
            gauth.flow.params.update({'approval_prompt': 'force'})

            gauth.LocalWebserverAuth()
        # Save the current credentials to a file
        gauth.SaveCredentialsFile("mycreds.txt")
        return GoogleDrive(gauth)

    def google_drive_upload(self, rec, file_path, bkp_file, bkp_file2, bkp_folder, status, date_today, db_content,
                            dbfile_content):
        StatusObj = self.env['auto.database.backup.status']
        # GOOGLE DRIVE UPLOAP
        if rec.backup_destination == "g_drive":
            try:
                drive = rec.authorize_drive()
                if status == 1:  # db file
                    db_backup_file = drive.CreateFile({'title': bkp_file})
                    db_backup_file.SetContentFile(file_path)
                    db_backup_file.Upload()
                else:  # db filed & folders
                    db_backup_file2 = drive.CreateFile({'title': bkp_folder})
                    db_backup_file2.SetContentFile(bkp_file2)
                    db_backup_file2.Upload()
                _logger.info("Backup Successfully Uploaded to Google Drive.")
                if os.path.exists(file_path):
                    os.remove(file_path)
                if rec.backup == 'db_only' and status == 1:
                    StatusObj.create({'date': date_today, 'name': "Google Drive: Success"})
                if rec.backup == 'db_and_files' and status == 2:
                    StatusObj.create({'date': date_today, 'name': "Success"})
                if rec.backup_id.bkup_email:
                    if rec.backup == 'db_only' and status == 1:
                        self.send_success_mail_notificaton(rec, bkp_file, bkp_folder)
                    if rec.backup == 'db_and_files' and status == 2:
                        self.send_success_mail_notificaton(rec, bkp_file2, bkp_folder)
                        # AUTO REMOVE UPLOADED FILE
                if rec.backup_id.autoremove:
                    file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
                    for item in file_list:
                        item_title = item['title']
                        if self.env.cr.dbname in item['title']:
                            date_today1 = datetime.datetime.today().date()
                            create_date = datetime.datetime.strptime(str(item['createdDate'])[0:10], '%Y-%m-%d').date()
                            delta = date_today1 - create_date
                            if delta.days >= rec.backup_id.days_to_keep:
                                # delete file from drive
                                drive.CreateFile({'id': item['id']}).Delete()
                                _logger.info("Deleted Google Drive out-of-date file %s." % (item_title,))
                        elif rec.backup == 'db_and_files' and rec.files_path.split('/')[-1] in item['title']:
                            date_today1 = datetime.datetime.today().date()
                            create_date = datetime.datetime.strptime(str(item['createdDate'])[0:10], '%Y-%m-%d').date()
                            delta1 = date_today1 - create_date
                            if delta1.days >= rec.backup_id.days_to_keep:
                                # delete folders from drive
                                drive.CreateFile({'id': item['id']}).Delete()
                                _logger.info("Deleted Google Drive out-of-date folders %s." % (item_title,))
                        else:
                            continue
            except Exception as e:
                _logger.debug("Backup Upload to Google drive Failed. Error: %s" % (str(e),))
                StatusObj.create({'date': date_today, 'name': "Failed (Error: %s)" % (str(e))})
                if rec.backup_id.bkup_fail_email:
                    self.send_fail_mail_notificaton(rec, bkp_file2, bkp_folder, str(e))

    def _take_dump(self, db_name, stream, model, backup_destination, backup_format='zip'):
        """Dump database `db` into file-like object `stream` if stream is None
        return a file object with the dump """

        cron_user_id = self.env.ref('auto_odoo_db_and_file_backup.auto_db_backup_scheduler').user_id.id
        if self._name != 'database.backup' or cron_user_id != self.env.user.id:
            _logger.error('Unauthorized database operation. Backups should only be available from the cron job.')
            raise AccessDenied()

        _logger.info('DUMP DB: %s format %s', db_name, backup_format)

        cmd = ['pg_dump', '--no-owner']
        cmd.append(db_name)
        env = exec_pg_environ()
        if backup_format == 'zip':
            with tempfile.TemporaryDirectory() as dump_dir:
                filestore = odoo.tools.config.filestore(db_name)
                if os.path.exists(filestore):
                    shutil.copytree(filestore, os.path.join(dump_dir, 'filestore'))
                with open(os.path.join(dump_dir, 'manifest.json'), 'w') as fh:
                    db = odoo.sql_db.db_connect(db_name)
                    with db.cursor() as cr:
                        json.dump(self._dump_db_manifest(cr), fh, indent=4)
                cmd.insert(-1, '--file=' + os.path.join(dump_dir, 'dump.sql'))
                subprocess.run(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=True)
                if stream:
                    odoo.tools.osutil.zip_dir(dump_dir, stream, include_dir=False,
                                              fnct_sort=lambda file_name: file_name != 'dump.sql')
                else:
                    t = tempfile.TemporaryFile()
                    odoo.tools.osutil.zip_dir(dump_dir, t, include_dir=False,
                                              fnct_sort=lambda file_name: file_name != 'dump.sql')
                    t.seek(0)
                    return t
        else:
            cmd.insert(-1, '--format=c')
            stdout = subprocess.Popen(cmd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE).stdout
            if stream:
                if backup_destination == "folder":
                    shutil.copyfileobj(stdout, stream)
                else:
                    try:
                        with open(stream, 'wb') as f:
                            f.write(stdout.read())
                    except Exception as e:
                        print("Error: ", e)
            else:
                return stdout

    def _dump_db_manifest(self, cr):
        pg_version = "%d.%d" % divmod(cr._obj.connection.server_version / 100, 100)
        cr.execute("SELECT name, latest_version FROM ir_module_module WHERE state = 'installed'")
        modules = dict(cr.fetchall())
        manifest = {
            'odoo_dump': '1',
            'db_name': cr.dbname,
            'version': odoo.release.version,
            'version_info': odoo.release.version_info,
            'major_version': odoo.release.major_version,
            'pg_version': pg_version,
            'modules': modules,
        }
        return manifest
