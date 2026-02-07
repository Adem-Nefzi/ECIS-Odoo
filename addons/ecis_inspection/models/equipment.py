from odoo import models, fields, api, _
from datetime import timedelta, date
from odoo.exceptions import ValidationError

class EcisEquipment(models.Model):
    """
    Equipment Model - Basic equipment information for inspections
    """
    _name = 'ecis.equipment'
    _description = 'Equipment to Inspect'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # ========== BASIC INFORMATION ==========
    name = fields.Char(
        string='Equipment Name',
        required=True,
        tracking=True,
        help="Name or reference of the equipment"
    )
    
    equipment_type = fields.Selection([
        ('crane', 'Crane'),
        ('elevator', 'Elevator'),
        ('pressure_vessel', 'Pressure Vessel'),
        ('forklift', 'Forklift'),
        ('overhead_crane', 'Overhead Crane'),
        ('lifting_platform', 'Lifting Platform'),
        ('other', 'Other')
    ], string='Equipment Type', required=True, tracking=True,
       help="Type of equipment to inspect")
    
    # ========== TECHNICAL DETAILS ==========
    brand = fields.Char(
        string='Brand',
        tracking=True,
        help="Manufacturer brand"
    )
    
    model = fields.Char(
        string='Model',
        help="Equipment model"
    )
    
    serial_number = fields.Char(
        string='Serial Number',
        copy=False,
        tracking=True,
        help="Unique serial number of the equipment"
    )
    
    manufacture_year = fields.Integer(
        string='Year of Manufacture',
        help="Year the equipment was manufactured"
    )
    
    capacity = fields.Char(
        string='Capacity/Load',
        help="Maximum capacity (e.g., 5 tons, 8 persons, etc.)"
    )
    
    # ========== CLIENT INFORMATION ==========
    client_id = fields.Many2one(
        'res.partner',
        string='Client',
        required=True,
        tracking=True,
        domain=[('is_company', '=', True)],
        help="Company that owns this equipment"
    )
    
    location = fields.Text(
        string='Exact Location',
        help="Precise address where the equipment is located"
    )
    
    # ========== INSPECTION TRACKING ==========
    last_inspection_date = fields.Date(
        string='Last Inspection Date',
        readonly=True,
        help="Date of the most recent completed inspection"
    )
    
    inspection_ids = fields.One2many(
        'ecis.inspection',
        'equipment_id',
        string='Inspections',
        help="All inspections performed on this equipment"
    )
    
    inspection_count = fields.Integer(
        string='Number of Inspections',
        compute='_compute_inspection_count',
        help="Total number of inspections performed"
    )
    
    # ========== OTHER FIELDS ==========
    active = fields.Boolean(
        default=True,
        help="Uncheck to archive this equipment"
    )
    
    notes = fields.Text(
        string='Additional Notes',
        help="Any additional remarks about this equipment"
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    
    # ========== COMPUTED FIELDS ==========
    
    @api.depends('inspection_ids')
    def _compute_inspection_count(self):
        """Count total inspections for this equipment"""
        for record in self:
            record.inspection_count = len(record.inspection_ids)
    
    # ========== CONSTRAINTS ==========
    
    @api.constrains('manufacture_year')
    def _check_manufacture_year(self):
        """Validate manufacture year is reasonable"""
        current_year = date.today().year
        for record in self:
            if record.manufacture_year:
                if record.manufacture_year > current_year:
                    raise ValidationError(_('Manufacture year cannot be in the future.'))
                if record.manufacture_year < 1900:
                    raise ValidationError(_('Manufacture year seems incorrect (before 1900).'))
    
    # ========== ACTIONS ==========
    
    def action_view_inspections(self):
        """Open list of all inspections for this equipment"""
        self.ensure_one()
        return {
            'name': _('Inspections - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'ecis.inspection',
            'view_mode': 'tree,form,calendar',
            'domain': [('equipment_id', '=', self.id)],
            'context': {
                'default_equipment_id': self.id,
                'default_client_id': self.client_id.id,
            }
        }
    
    def action_schedule_inspection(self):
        """Open form to schedule new inspection"""
        self.ensure_one()
        return {
            'name': _('Schedule Inspection'),
            'type': 'ir.actions.act_window',
            'res_model': 'ecis.inspection',
            'view_mode': 'form',
            'context': {
                'default_equipment_id': self.id,
                'default_client_id': self.client_id.id,
                'default_inspection_date': date.today(),
            },
            'target': 'current',
        }
    
    # ========== NAME DISPLAY ==========
    
    def name_get(self):
        """Display equipment name with type"""
        result = []
        for record in self:
            type_label = dict(record._fields['equipment_type'].selection).get(record.equipment_type, '')
            name = f"[{type_label}] {record.name}"
            if record.serial_number:
                name += f" - S/N: {record.serial_number}"
            result.append((record.id, name))
        return result