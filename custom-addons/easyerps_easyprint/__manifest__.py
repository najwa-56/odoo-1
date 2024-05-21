{
    'name': 'Easy Print',
    'support': "support@easyerps.com",
    'license': "OPL-1",
    'price': 269,
    'currency': "USD",
    'version': '17.1.0',
    'description': 'Direct Print',
    'depends': [
        'base','web'
    ],
    'auto_install': False,
    'application': False,
    'assets': {
        'web.assets_backend': [
            'easyerps_easyprint/static/src/js/action_service.js'
        ],

    },
    'images': ['images/main_screenshot.png'],
}