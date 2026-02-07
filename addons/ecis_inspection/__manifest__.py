{
    'name': 'ECIS Inspection Management',
    'version': '1.0.0',
    'category': 'Services/Inspection',
    'summary': 'Complete inspection management with PDF reports',
    'description': '''
        ECIS Inspection Module
        ======================
        
        Features:
        * Equipment registration
        * Inspection report creation
        * Customizable checklists
        * PDF report generation with signatures
        * Calendar view for scheduling
        
        Developed by: Nefzi Adem
    ''',
    'author': 'Nefzi Adem - ECIS-DZ',
    'depends': ['base', 'mail', 'contacts', 'portal'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'data/checklist_templates.xml',
        'views/equipment_views.xml',
        'views/inspection_views.xml',
        'views/menu_views.xml',
        'reports/inspection_report.xml',
        'reports/inspection_report_template.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}