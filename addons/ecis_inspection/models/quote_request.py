# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re

class EcisQuoteRequest(models.Model):
    """
    Quote/Contact Request from Website
    Stores inquiries from potential clients
    """
    _name = 'ecis.quote.request'
    _description = 'Quote Request from Website'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ========== BASIC INFORMATION ==========
    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New',
        help="Unique reference number"
    )
    
    # ========== CONTACT INFORMATION ==========
    contact_name = fields.Char(
        string='Full Name',
        required=True,
        tracking=True,
        help="Person making the request"
    )
    
    email = fields.Char(
        string='Email',
        required=True,
        tracking=True,
        help="Contact email address"
    )
    
    phone = fields.Char(
        string='Phone Number',
        required=True,
        tracking=True,
        help="Contact phone number"
    )
    
    company_name = fields.Char(
        string='Company Name',
        help="Company name if applicable"
    )
    
    # ========== REQUEST DETAILS ==========
    equipment_type = fields.Selection([
        ('crane', 'Crane'),
        ('elevator', 'Elevator'),
        ('pressure_vessel', 'Pressure Vessel'),
        ('forklift', 'Forklift'),
        ('overhead_crane', 'Overhead Crane'),
        ('lifting_platform', 'Lifting Platform'),
        ('other', 'Other')
    ], string='Equipment Type', required=True, tracking=True)
    
    equipment_count = fields.Integer(
        string='Number of Equipment',
        default=1,
        help="How many pieces of equipment need inspection"
    )
    
    message = fields.Text(
        string='Message',
        help="Additional details about the request"
    )
    
    urgency = fields.Selection([
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency')
    ], string='Urgency', default='normal')
    
    # ========== LOCATION ==========
    location = fields.Text(
        string='Location',
        help="Where is the equipment located"
    )
    
    # ========== SOURCE ==========
    source = fields.Selection([
        ('website', 'Website'),
        ('phone', 'Phone Call'),
        ('email', 'Email'),
        ('referral', 'Referral'),
        ('other', 'Other')
    ], string='Source', default='website', help="How did they contact us")
    
    # ========== STATUS ==========
    state = fields.Selection([
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('quoted', 'Quote Sent'),
        ('converted', 'Converted to Client'),
        ('lost', 'Lost')
    ], string='Status', default='new', required=True, tracking=True)
    
    # ========== ASSIGNMENT ==========
    assigned_to = fields.Many2one(
        'res.users',
        string='Assigned To',
        tracking=True,
        help="Sales person assigned to this request"
    )
    
    # ========== CONVERSION ==========
    partner_id = fields.Many2one(
        'res.partner',
        string='Converted to Client',
        help="Client created from this request"
    )
    
    # ========== METADATA ==========
    active = fields.Boolean(default=True)
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    
    # ========== IP TRACKING (OPTIONAL) ==========
    ip_address = fields.Char(
        string='IP Address',
        help="IP address of the requester"
    )
    
    user_agent = fields.Char(
        string='User Agent',
        help="Browser user agent"
    )
    
    # ========== COMPUTED FIELDS ==========
    @api.model
    def create(self, vals):
        """Generate sequence number on creation"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('ecis.quote.request') or 'New'
        
        # Auto-assign to user if configured
        if not vals.get('assigned_to'):
            default_user = self.env['ir.config_parameter'].sudo().get_param('ecis_inspection.default_sales_user')
            if default_user:
                vals['assigned_to'] = int(default_user)
        
        result = super(EcisQuoteRequest, self).create(vals)
        
        # Send notification to sales team
        result._send_new_request_notification()
        
        return result
    
    # ========== VALIDATION ==========
    @api.constrains('email')
    def _check_email(self):
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for record in self:
            if record.email and not re.match(email_pattern, record.email):
                raise ValidationError(_('Invalid email format: %s') % record.email)
    
    @api.constrains('phone')
    def _check_phone(self):
        """Validate phone has minimum length"""
        for record in self:
            if record.phone:
                # Remove spaces, dashes, parentheses
                cleaned = re.sub(r'[\s\-\(\)]', '', record.phone)
                if len(cleaned) < 8:
                    raise ValidationError(_('Phone number seems too short'))
    
    # ========== ACTIONS ==========
    def action_contact_client(self):
        """Mark as contacted"""
        self.ensure_one()
        self.write({'state': 'contacted'})
        self.message_post(body=_('Client contacted by %s') % self.env.user.name)
    
    def action_send_quote(self):
        """Mark as quote sent"""
        self.ensure_one()
        self.write({'state': 'quoted'})
        self.message_post(body=_('Quote sent to client'))
    
    def action_convert_to_client(self):
        """Convert to actual client (res.partner)"""
        self.ensure_one()
        
        # Create partner if not exists
        if not self.partner_id:
            partner_vals = {
                'name': self.company_name or self.contact_name,
                'email': self.email,
                'phone': self.phone,
                'is_company': bool(self.company_name),
                'comment': f'Created from quote request {self.name}\nOriginal message: {self.message or ""}',
            }
            partner = self.env['res.partner'].create(partner_vals)
            self.write({
                'partner_id': partner.id,
                'state': 'converted'
            })
            self.message_post(body=_('Converted to client: %s') % partner.name)
            
            return {
                'name': _('Client Created'),
                'type': 'ir.actions.act_window',
                'res_model': 'res.partner',
                'res_id': partner.id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            self.write({'state': 'converted'})
    
    def action_mark_lost(self):
        """Mark as lost opportunity"""
        self.ensure_one()
        self.write({'state': 'lost'})
        self.message_post(body=_('Marked as lost by %s') % self.env.user.name)
    
    # ========== NOTIFICATIONS ==========
    def _send_new_request_notification(self):
        """Send email notification to sales team"""
        self.ensure_one()
        
        # Get email template
        template = self.env.ref('ecis_inspection.email_template_new_quote_request', raise_if_not_found=False)
        
        if template and self.assigned_to and self.assigned_to.email:
            template.send_mail(self.id, force_send=False)