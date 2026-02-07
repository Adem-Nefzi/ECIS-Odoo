from odoo import models, fields, api

class EcisInspectionChecklist(models.Model):
    """
    Inspection Checklist Items - Individual check points during inspection
    """
    _name = 'ecis.inspection.checklist'
    _description = 'Inspection Checklist Item'
    _order = 'sequence, id'

    inspection_id = fields.Many2one(
        'ecis.inspection',
        string='Inspection',
        required=True,
        ondelete='cascade',
        help="Parent inspection report"
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Display order"
    )
    
    name = fields.Char(
        string='Check Item',
        required=True,
        help="What needs to be checked"
    )
    
    requirement = fields.Char(
        string='Requirement/Standard',
        help="Regulatory requirement or standard reference"
    )
    
    status = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('warning', 'Warning'),
        ('na', 'Not Applicable')
    ], string='Status', required=True, default='pass',
       help="Result of this check item")
    
    notes = fields.Text(
        string='Notes',
        help="Additional observations or details"
    )
    
    photo = fields.Binary(
        string='Photo',
        attachment=True,
        help="Photo evidence for this item"
    )
    
    photo_filename = fields.Char(string='Photo Filename')


class EcisChecklistTemplate(models.Model):
    """
    Checklist Templates - Predefined checklist items for different equipment types
    """
    _name = 'ecis.checklist.template'
    _description = 'Inspection Checklist Template'
    _order = 'equipment_type, sequence'

    name = fields.Char(
        string='Check Item',
        required=True,
        help="Standard check item description"
    )
    
    equipment_type = fields.Selection([
        ('crane', 'Crane'),
        ('elevator', 'Elevator'),
        ('pressure_vessel', 'Pressure Vessel'),
        ('forklift', 'Forklift'),
        ('overhead_crane', 'Overhead Crane'),
        ('lifting_platform', 'Lifting Platform'),
        ('other', 'Other')
    ], string='Equipment Type', required=True,
       help="Type of equipment this check applies to")
    
    requirement = fields.Char(
        string='Requirement/Standard',
        help="Regulatory standard or requirement"
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Display order in checklist"
    )
    
    active = fields.Boolean(
        default=True,
        help="Uncheck to disable this template item"
    )
    
    description = fields.Text(
        string='Description',
        help="Detailed description of what to check"
    )