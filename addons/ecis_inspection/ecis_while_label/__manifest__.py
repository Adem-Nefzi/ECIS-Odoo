# -*- coding: utf-8 -*-
{
    'name': 'ECIS-DZ White Label',
    'version': '1.0',
    'category': 'Customizations',
    'summary': 'ECIS-DZ Custom Branding',
    'description': """
        Remove Odoo branding and replace with ECIS-DZ branding
        - Custom logo
        - Custom colors
        - Custom company info
        - Remove "Powered by Odoo"
    """,
    'author': 'ECIS-DZ',
    'website': 'https://ecis-dz.com',
    'depends': ['web', 'base'],
    'data': [
        'views/webclient_templates.xml',
    ],
    'assets': {
    'web.assets_backend': [
        'ecis_white_label/static/src/css/ecis_branding.css',
        'ecis_white_label/static/src/xml/webclient_templates.xml',
    ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}