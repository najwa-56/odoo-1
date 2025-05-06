# -*- coding: utf-8 -*-
#################################################################################
# Author      : CFIS (<https://www.cfis.store/>)
# Copyright(c): 2017-Present CFIS.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://www.cfis.store/>
#################################################################################

{
    "name": "Google Map View | Contacts Google Map View | Partners Google Map View | Map View",
    "summary": """
        This Odoo module adds a map view to the contact model using existing latitude and longitude fields. 
        It allows you to display the location on the map and enables users to change the location by dragging the marker.
        """,
    "version": "17.1",
    "description": """
        This Odoo module adds a map view to the contact model using existing latitude and longitude fields. 
        It allows you to display the location on the map and enables users to change the location by dragging the marker.
        """,    
    "author": "CFIS",
    "maintainer": "CFIS",
    "license" :  "Other proprietary",
    "website": "https://www.cfis.store",
    "images": ["images/web_googlemap.png"],
    "category": "Extra Tools",
    "depends": [
        "web",
        "contacts",
        "base_setup",
        "base_geolocalize",
    ],
    "data": [
        "views/res_config_settings.xml",
        "views/res_partner_views.xml",
        "views/contact_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/web_googlemap/static/src/**/*", 
        ],
    },
    "installable": True,
    "application": True,
    "price"                 :  85,
    "currency"              :  "EUR",
    "pre_init_hook"         :  "pre_init_check",
}
