# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta

class EcisEquipment(models.Model):
    _name = 'ecis.equipment'
    _description = 'Equipment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Equipment Name', required=True, tracking=True)
    
    type_equipement = fields.Selection([
        ('grue', 'Crane'),
        ('ascenseur', 'Elevator'),
        ('appareil_pression', 'Pressure Vessel'),
        ('chariot_elevateur', 'Forklift'),
        ('autre', 'Other')
    ], string='Type', required=True, tracking=True)
    
    marque = fields.Char(string='Brand')
    modele = fields.Char(string='Model')
    numero_serie = fields.Char(string='Serial Number')
    
    client_id = fields.Many2one('res.partner', string='Client', required=True, tracking=True)
    
    periodicite = fields.Integer(string='Period (months)', default=12, required=True)
    derniere_inspection = fields.Date(string='Last Inspection')
    prochaine_echeance = fields.Date(string='Next Due Date', compute='_compute_echeance', store=True)
    
    active = fields.Boolean(default=True)
    
    @api.depends('derniere_inspection', 'periodicite')
    def _compute_echeance(self):
        for record in self:
            if record.derniere_inspection and record.periodicite:
                record.prochaine_echeance = record.derniere_inspection + timedelta(days=record.periodicite * 30)
            else:
                record.prochaine_echeance = False