# -*- coding: utf-8 -*-
{
    'name': 'ECIS White Label',
    'version': '1.0.1',
    'category': 'Tools',
    'summary': 'Simple ECIS branding for web UI',
    'description': """
ECIS White Label
================
Small UI branding tweaks for the web client.
""",
    'author': 'ECIS-DZ',
    'website': 'https://ecis-dz.com',
    'depends': ['web'],
    'data': [
        'views/webclient_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ecis_white_label/static/src/css/ecis_branding.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}