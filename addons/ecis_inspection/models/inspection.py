from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class EcisInspection(models.Model):
    """
    Inspection Model - Manages inspection reports and results
    """
    _name = 'ecis.inspection'
    _description = 'Equipment Inspection Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'inspection_date desc, id desc'

    # ========== BASIC INFORMATION ==========
    name = fields.Char(
        string='Report Number',
        required=True,
        copy=False,
        readonly=True,
        default='New',
        help="Unique inspection report number"
    )
    
    # ========== EQUIPMENT & CLIENT ==========
    equipment_id = fields.Many2one(
        'ecis.equipment',
        string='Equipment',
        required=True,
        tracking=True,
        help="Equipment being inspected"
    )
    
    client_id = fields.Many2one(
        related='equipment_id.client_id',
        string='Client',
        store=True,
        readonly=True,
        help="Client who owns the equipment"
    )
    
    equipment_type = fields.Selection(
        related='equipment_id.equipment_type',
        string='Equipment Type',
        readonly=True,
        store=True
    )
    
    # ========== INSPECTION DETAILS ==========
    inspection_date = fields.Date(
        string='Inspection Date',
        default=fields.Date.today,
        required=True,
        tracking=True,
        help="Date when inspection was performed"
    )
    
    inspector_id = fields.Many2one(
        'res.users',
        string='Inspector',
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
        help="Person who performed the inspection"
    )
    
    inspection_type = fields.Selection([
        ('initial', 'Initial Inspection'),
        ('periodic', 'Periodic Inspection'),
        ('after_repair', 'After Repair Inspection'),
        ('emergency', 'Emergency Inspection'),
        ('special', 'Special Inspection')
    ], string='Inspection Type', required=True, default='periodic',
       tracking=True, help="Type of inspection being performed")
    
    inspection_duration = fields.Float(
        string='Duration (hours)',
        help="Time spent on inspection in hours"
    )
    
    weather_conditions = fields.Char(
        string='Weather Conditions',
        help="Weather conditions during inspection (for outdoor equipment)"
    )
    
    # ========== CHECKLIST ==========
    checklist_ids = fields.One2many(
        'ecis.inspection.checklist',
        'inspection_id',
        string='Inspection Checklist',
        help="Detailed checklist items"
    )
    
    checklist_pass_count = fields.Integer(
        string='Passed Items',
        compute='_compute_checklist_stats',
        help="Number of checklist items that passed"
    )
    
    checklist_fail_count = fields.Integer(
        string='Failed Items',
        compute='_compute_checklist_stats',
        help="Number of checklist items that failed"
    )
    
    checklist_total_count = fields.Integer(
        string='Total Items',
        compute='_compute_checklist_stats',
        help="Total checklist items"
    )
    
    # ========== RESULTS ==========
    overall_result = fields.Selection([
        ('approved', 'Approved'),
        ('conditional', 'Conditional - Requires Follow-up'),
        ('rejected', 'Rejected - Not Safe for Use')
    ], string='Overall Result', tracking=True,
       help="Final inspection verdict")
    
    defects_found = fields.Text(
        string='Defects Found',
        help="Description of any defects or issues found"
    )
    
    immediate_actions_required = fields.Text(
        string='Immediate Actions Required',
        help="Actions that must be taken immediately"
    )
    
    recommendations = fields.Text(
        string='Recommendations',
        help="Recommendations for maintenance or improvements"
    )
    
    inspector_notes = fields.Text(
        string='Inspector Notes',
        help="Additional notes from the inspector"
    )
    
    # ========== SIGNATURE & DOCUMENTATION ==========
    inspector_signature = fields.Binary(
        string='Inspector Signature',
        attachment=True,
        help="Electronic signature of the inspector"
    )
    
    client_signature = fields.Binary(
        string='Client Signature',
        attachment=True,
        help="Electronic signature of client representative"
    )
    
    client_representative = fields.Char(
        string='Client Representative Name',
        help="Name of person who signed on behalf of client"
    )
    
    photo_ids = fields.Many2many(
        'ir.attachment',
        string='Photos',
        help="Photos taken during inspection"
    )
    
    # ========== PDF REPORT ==========
    report_pdf = fields.Binary(
        string='PDF Report',
        attachment=True,
        readonly=True,
        help="Generated PDF inspection report"
    )
    
    report_pdf_name = fields.Char(
        string='PDF Filename',
        compute='_compute_report_pdf_name'
    )
    
    # ========== NEXT INSPECTION ==========
    next_inspection_due = fields.Date(
        string='Next Inspection Due Date',
        help="When the next inspection should be performed"
    )
    
    next_inspection_frequency = fields.Integer(
        string='Next Inspection In (months)',
        help="Months until next inspection is due"
    )
    
    # ========== WORKFLOW ==========
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('sent', 'Sent to Client'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True,
       tracking=True, help="Current status of the inspection")
    
    # ========== OTHER ==========
    active = fields.Boolean(default=True)
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    
    # ========== COMPUTED FIELDS ==========
    
    @api.depends('checklist_ids', 'checklist_ids.status')
    def _compute_checklist_stats(self):
        """Calculate checklist statistics"""
        for record in self:
            total = len(record.checklist_ids)
            passed = len(record.checklist_ids.filtered(lambda c: c.status == 'pass'))
            failed = len(record.checklist_ids.filtered(lambda c: c.status == 'fail'))
            
            record.checklist_total_count = total
            record.checklist_pass_count = passed
            record.checklist_fail_count = failed
    
    @api.depends('name')
    def _compute_report_pdf_name(self):
        """Generate PDF filename"""
        for record in self:
            if record.name and record.name != 'New':
                record.report_pdf_name = f'{record.name}_Inspection_Report.pdf'
            else:
                record.report_pdf_name = 'Inspection_Report.pdf'
    
    # ========== LIFECYCLE METHODS ==========
    
    @api.model
    def create(self, vals):
        """Generate sequence number on creation"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('ecis.inspection') or 'New'
        return super(EcisInspection, self).create(vals)
    
    # ========== CONSTRAINTS ==========
    
    @api.constrains('inspection_date')
    def _check_inspection_date(self):
        """Inspection date cannot be in the future"""
        for record in self:
            if record.inspection_date and record.inspection_date > fields.Date.today():
                raise ValidationError(_('Inspection date cannot be in the future.'))
    
    @api.constrains('overall_result', 'state')
    def _check_result_before_completion(self):
        """Overall result is required before completing"""
        for record in self:
            if record.state == 'completed' and not record.overall_result:
                raise ValidationError(_('Please set the overall result before completing the inspection.'))
    
    # ========== ONCHANGE METHODS ==========
    
    @api.onchange('equipment_id')
    def _onchange_equipment_id(self):
        """Load default checklist based on equipment type"""
        if self.equipment_id and not self.checklist_ids:
            # Get template checklist for this equipment type
            template_items = self.env['ecis.checklist.template'].search([
                ('equipment_type', '=', self.equipment_id.equipment_type)
            ])
            
            checklist_lines = []
            for template in template_items:
                checklist_lines.append((0, 0, {
                    'name': template.name,
                    'requirement': template.requirement,
                    'sequence': template.sequence,
                    'status': 'pass',  # Default to pass
                }))
            
            self.checklist_ids = checklist_lines
    
    @api.onchange('next_inspection_frequency')
    def _onchange_next_inspection_frequency(self):
        """Calculate next inspection due date"""
        if self.inspection_date and self.next_inspection_frequency:
            from datetime import timedelta
            days = self.next_inspection_frequency * 30
            self.next_inspection_due = self.inspection_date + timedelta(days=days)
    
    # ========== ACTION METHODS ==========
    
    def action_start_inspection(self):
        """Start the inspection process"""
        self.ensure_one()
        self.write({'state': 'in_progress'})
        self.message_post(body=_('Inspection started.'))
    
    def action_complete_inspection(self):
        """Mark inspection as completed and update equipment"""
        for record in self:
            if not record.overall_result:
                raise UserError(_('Please set the overall result before completing.'))
        
            if not record.inspector_signature:
                raise UserError(_('Inspector signature is required before completing.'))
        
            # Update state
            record.write({'state': 'completed'})
        
        # Update equipment last inspection date
            record.equipment_id.write({
            'last_inspection_date': record.inspection_date,
        })
        
        # Note: Next inspection date removed from simplified equipment model
    
    def action_generate_pdf(self):
        """Generate PDF inspection report - triggers native report"""
        self.ensure_one()
        return self.env.ref('ecis_inspection.action_report_inspection').report_action(self)
    
    def action_send_to_client(self):
        """Send inspection report to client via email"""
        self.ensure_one()
        
        # Just update state - email functionality can be added later
        self.write({'state': 'sent'})
        self.message_post(body=_('Inspection marked as sent to client.'))
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Inspection marked as sent. Use Print button to generate PDF.'),
                'type': 'success',
            }
        }
    
    def action_cancel(self):
        """Cancel the inspection"""
        self.ensure_one()
        self.write({'state': 'cancelled'})
        self.message_post(body=_('Inspection cancelled.'))
    
    def action_reset_to_draft(self):
        """Reset inspection to draft"""
        self.ensure_one()
        self.write({'state': 'draft'})
        self.message_post(body=_('Reset to draft.'))
    
    def action_download_pdf(self):
        """Download the PDF report"""
        self.ensure_one()
        return self.env.ref('ecis_inspection.action_report_inspection').report_action(self)