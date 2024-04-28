# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    'name': "Activities Management-Advance",
    'author': 'Softhealer Technologies',
    'website': 'https://www.softhealer.com',
    "support": "support@softhealer.com",
    'category': 'Discuss',
    "license": "OPL-1",
    'version': '0.0.8',
    "summary": "Activity Management Activity Scheduler Manage Employee Activity Manage Supervisor Activity filter Activity Manage Multi Activities Schedule Mass Activities Dynamic Action For Multiple Activities Manage Activity Scheduler Employee Activity Supervisor Activity filter Activity Multi Activity Schedule Mass Activity Tag activity history Activity monitoring Activity multi users assign schedule activity schedule activities Multi Company Activity Mail Odoo Activity Management Activity Dashboard Activity Monitoring Activity Views User Activity Log, User Activity Audit,  Session Management, Record Log, Activity Traces, Login Notification, User Activity Record, Record History, Login History, Login location, Login IP Advance Schedule Activity multi users assign schedule activity to multi users Schedule Activity Dashboard for schedule activity history of schedule activity reports for schedule activity menu and view for schedule activities for Multi Company Activity Portal Activity At Portal Activities Portal odoo",
    "description": """Do you want to show the activities list beautifully? Do you want to show the well-organized structure of activities? Do you want to show completed, uncompleted activities easily to your employees? Do you want to show an activity dashboard to the employee? Do you want to manage activities nicely with odoo? Do you want to show the scheduled activity to the manager, supervisor & employee? This module helps the manager can see everyone's activity, the supervisor can see the assigned user and own activity, the user can see only own activity. Everyone can filter activity by the previous year, previous month, previous week, today, yesterday, tomorrow, weekly, monthly, yearly & custom date. You can see activities like all activities, planned activities, completed activities or overdue activities. Manager, Supervisor & Employee have their own dashboard, that provides a beautiful design on the dashboard. Hurray!""",
    'depends': [
        'bus',
        'sh_activity_base',
        'portal'
    ],
    'data': [
       'activity_menu_dashboard.xml'
    ],
    'images': [ ],

    'assets': {
        'web.assets_backend': [

            ],     
        'web.assets_frontend': [

        ],
        },
}
