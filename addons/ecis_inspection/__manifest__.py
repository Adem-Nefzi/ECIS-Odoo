# -*- coding: utf-8 -*-
{
    'name': 'ECIS Inspection Management',
    'version': '1.0.0',
    'category': 'Services',
    'summary': 'Module Inspection - Nefzi Adem',
    'author': 'Nefzi Adem',
    'depends': ['base', 'mail', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/equipment_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
}