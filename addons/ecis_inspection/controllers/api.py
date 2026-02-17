import base64
import json
from datetime import date, datetime

from odoo import http, fields
from odoo.exceptions import ValidationError, UserError
from odoo.http import request


class EcisInspectionApiController(http.Controller):
    def _add_cors_headers(self, response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-API-Key, Accept'
        return response

    def _json_default(self, value):
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        if isinstance(value, bytes):
            return base64.b64encode(value).decode('ascii')
        return str(value)

    def _json_response(self, payload, status=200):
        body = json.dumps(payload, default=self._json_default)
        response = request.make_response(
            body,
            headers=[('Content-Type', 'application/json')],
            status=status,
        )
        return self._add_cors_headers(response)

    def _error_response(self, message, status=400, details=None):
        payload = {'success': False, 'error': message}
        if details is not None:
            payload['details'] = details
        return self._json_response(payload, status=status)

    def _get_payload(self):
        payload = {}

        json_body = request.httprequest.get_json(silent=True)
        if isinstance(json_body, dict):
            payload.update(json_body)
        elif json_body is not None:
            payload['_raw'] = json_body

        form_data = request.httprequest.form
        if form_data:
            payload.update(form_data.to_dict())

        args_data = request.httprequest.args
        if args_data:
            payload.update(args_data.to_dict())

        if not payload:
            raw = request.httprequest.data
            if raw:
                try:
                    parsed = json.loads(raw.decode('utf-8'))
                    if isinstance(parsed, dict):
                        payload.update(parsed)
                    else:
                        payload['_raw'] = parsed
                except Exception:
                    payload['_raw'] = raw.decode('utf-8', 'replace')

        return payload

    def _get_api_key(self):
        return request.env['ir.config_parameter'].sudo().get_param('ecis_inspection.api_key')

    def _extract_api_key(self):
        header_key = request.httprequest.headers.get('X-API-Key')
        auth_header = request.httprequest.headers.get('Authorization')
        if auth_header and auth_header.lower().startswith('bearer '):
            return auth_header.split(' ', 1)[1].strip()
        if header_key:
            return header_key.strip()
        return request.params.get('api_key')

    def _require_api_key(self):
        expected = self._get_api_key()
        provided = self._extract_api_key()
        if not expected or not provided or provided != expected:
            return self._error_response('Unauthorized', status=401)
        return None

    def _parse_bool(self, value):
        return str(value).lower() in ('1', 'true', 'yes', 'on')

    def _parse_int(self, value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _get_company(self):
        company = request.env.company
        if company and company.id:
            return company
        return request.env['res.company'].sudo().search([], limit=1)

    def _get_company_required(self):
        company = self._get_company()
        if not company:
            raise ValidationError('No company found to assign records.')
        return company

    def _company_env(self, model_name):
        company = self._get_company_required()
        return request.env[model_name].sudo().with_company(company).with_context(
            allowed_company_ids=[company.id],
        )

    def _get_inspector_user_id(self):
        param_env = request.env['ir.config_parameter'].sudo()
        for key in ('ecis_inspection.default_inspector_user', 'ecis_inspection.default_sales_user'):
            value = param_env.get_param(key)
            if value:
                return int(value)
        user = request.env.user
        if user and user.id:
            return user.id
        admin = request.env.ref('base.user_admin', raise_if_not_found=False)
        if admin:
            return admin.id
        fallback = request.env['res.users'].sudo().search([('active', '=', True)], limit=1)
        return fallback.id if fallback else False

    def _serialize_partner(self, partner):
        return {
            'id': partner.id,
            'name': partner.name,
            'email': partner.email,
            'phone': partner.phone,
            'is_company': partner.is_company,
            'parent_id': partner.parent_id.id if partner.parent_id else False,
        }

    def _serialize_equipment(self, record):
        return {
            'id': record.id,
            'name': record.name,
            'equipment_type': record.equipment_type,
            'brand': record.brand,
            'model': record.model,
            'serial_number': record.serial_number,
            'manufacture_year': record.manufacture_year,
            'capacity': record.capacity,
            'location': record.location,
            'client_id': record.client_id.id,
        }

    def _serialize_checklist_item(self, item):
        return {
            'id': item.id,
            'inspection_id': item.inspection_id.id,
            'sequence': item.sequence,
            'name': item.name,
            'requirement': item.requirement,
            'status': item.status,
            'notes': item.notes,
        }

    def _serialize_inspection(self, record, include_checklist=False):
        data = {
            'id': record.id,
            'name': record.name,
            'inspection_date': record.inspection_date and record.inspection_date.isoformat(),
            'inspection_type': record.inspection_type,
            'inspection_duration': record.inspection_duration,
            'state': record.state,
            'overall_result': record.overall_result,
            'client': {
                'id': record.client_id.id,
                'name': record.client_id.name,
                'email': record.client_id.email,
                'phone': record.client_id.phone,
            },
            'equipment': {
                'id': record.equipment_id.id,
                'name': record.equipment_id.name,
                'type': record.equipment_type,
                'brand': record.equipment_id.brand,
                'serial_number': record.equipment_id.serial_number,
            },
            'inspector': {
                'id': record.inspector_id.id,
                'name': record.inspector_id.name,
            },
            'defects_found': record.defects_found,
            'recommendations': record.recommendations,
            'immediate_actions_required': record.immediate_actions_required,
            'inspector_notes': record.inspector_notes,
            'next_inspection_due': record.next_inspection_due and record.next_inspection_due.isoformat(),
            'next_inspection_frequency': record.next_inspection_frequency,
        }
        if include_checklist:
            data['checklist'] = [self._serialize_checklist_item(i) for i in record.checklist_ids]
        return data

    def _serialize_quote_request(self, record):
        return {
            'id': record.id,
            'reference': record.name,
            'contact_name': record.contact_name,
            'email': record.email,
            'phone': record.phone,
            'company_name': record.company_name,
            'equipment_type': record.equipment_type,
            'equipment_count': record.equipment_count,
            'message': record.message,
            'urgency': record.urgency,
            'location': record.location,
            'source': record.source,
            'state': record.state,
            'partner_id': record.partner_id.id if record.partner_id else False,
            'assigned_to': record.assigned_to.id if record.assigned_to else False,
        }

    def _get_equipment_type_label(self, equipment_type):
        selection = request.env['ecis.equipment']._fields['equipment_type'].selection
        return dict(selection).get(equipment_type, equipment_type)

    def _find_or_create_company(self, data):
        company_name = data.get('company_name') or data.get('name')
        partner_env = request.env['res.partner'].sudo()
        company = False
        if data.get('email'):
            company = partner_env.search([
                ('email', '=', data.get('email')),
                ('is_company', '=', True),
            ], limit=1)
        if not company and company_name:
            company = partner_env.search([
                ('name', '=', company_name),
                ('is_company', '=', True),
            ], limit=1)
        if not company:
            company = partner_env.create({
                'name': company_name,
                'email': data.get('email'),
                'phone': data.get('phone'),
                'is_company': True,
                'comment': 'Created from website quote request.',
            })
        return company

    def _find_or_create_contact(self, data, company):
        partner_env = request.env['res.partner'].sudo()
        contact = False
        if data.get('email'):
            contact = partner_env.search([
                ('email', '=', data.get('email')),
                ('parent_id', '=', company.id),
            ], limit=1)
        if not contact:
            contact = partner_env.create({
                'name': data.get('name'),
                'email': data.get('email'),
                'phone': data.get('phone'),
                'parent_id': company.id,
                'type': 'contact',
                'is_company': False,
            })
        return contact

    def _create_equipment(self, data, company, quote):
        equipment_type = data.get('equipment_type')
        equipment_label = self._get_equipment_type_label(equipment_type)
        equipment_name = f'{equipment_label} - {company.name}'
        equipment_notes = (
            f'Quote request reference: {quote.name}\n'
            f'Equipment count: {data.get("equipment_count", 1)}\n'
            f'Contact: {data.get("name")}\n'
            f'Phone: {data.get("phone")}\n'
            f'Email: {data.get("email")}\n'
            f'Message: {data.get("message") or ""}'
        )
        equipment_env = self._company_env('ecis.equipment')
        company_id = self._get_company_required().id
        return equipment_env.create({
            'name': equipment_name,
            'equipment_type': equipment_type,
            'client_id': company.id,
            'company_id': company_id,
            'serial_number': data.get('serial_number'),
            'location': data.get('location'),
            'notes': equipment_notes,
        })

    def _create_inspection(self, data, equipment, quote):
        inspection_notes = (
            f'Created from quote request {quote.name}.\n'
            f'Equipment count: {data.get("equipment_count", 1)}\n'
            f'Contact: {data.get("name")}\n'
            f'Phone: {data.get("phone")}\n'
            f'Email: {data.get("email")}\n'
            f'Message: {data.get("message") or ""}'
        )
        inspection_env = self._company_env('ecis.inspection')
        inspector_id = self._get_inspector_user_id()
        if not inspector_id:
            raise ValidationError('No inspector user available for inspection.')
        return inspection_env.create({
            'equipment_id': equipment.id,
            'inspection_type': 'initial',
            'inspection_date': fields.Date.today(),
            'inspector_notes': inspection_notes,
            'inspector_id': inspector_id,
            'company_id': self._get_company_required().id,
        })

    @http.route('/api/<path:subpath>', type='http', auth='none', methods=['OPTIONS'], csrf=False, cors='*')
    def api_options(self, subpath=None, **_params):
        response = request.make_response('', headers=[('Content-Type', 'text/plain')], status=204)
        return self._add_cors_headers(response)

    @http.route('/api/quote-request', type='http', auth='none', methods=['OPTIONS'], csrf=False, cors='*')
    def quote_request_options(self, **_params):
        response = request.make_response('', headers=[('Content-Type', 'text/plain')], status=204)
        return self._add_cors_headers(response)

    @http.route('/api/quote-request', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    def create_quote_request(self, **_params):
        try:
            data = self._get_payload()
            required_fields = ['name', 'email', 'phone', 'equipment_type']
            missing = [f for f in required_fields if not data.get(f)]
            if missing:
                return self._error_response(
                    f'Missing required fields: {", ".join(missing)}', status=400
                )

            ip_address = request.httprequest.remote_addr
            user_agent = request.httprequest.headers.get('User-Agent', '')

            quote = request.env['ecis.quote.request'].sudo().create({
                'contact_name': data.get('name'),
                'email': data.get('email'),
                'phone': data.get('phone'),
                'company_name': data.get('company_name'),
                'equipment_type': data.get('equipment_type'),
                'equipment_count': self._parse_int(data.get('equipment_count', 1), 1),
                'message': data.get('message'),
                'urgency': data.get('urgency', 'normal'),
                'location': data.get('location'),
                'source': 'website',
                'ip_address': ip_address,
                'user_agent': user_agent,
            })

            company = self._find_or_create_company(data)
            contact = self._find_or_create_contact(data, company)
            equipment = self._create_equipment(data, company, quote)
            inspection = self._create_inspection(data, equipment, quote)

            quote.sudo().write({
                'partner_id': company.id,
            })

            return self._json_response({
                'success': True,
                'message': 'Quote request submitted successfully. We will contact you within 24 hours.',
                'data': {
                    'reference': quote.name,
                    'quote_request_id': quote.id,
                    'company_id': company.id,
                    'contact_id': contact.id,
                    'equipment_id': equipment.id,
                    'inspection_id': inspection.id,
                    'inspection_reference': inspection.name,
                },
            }, status=201)

        except ValidationError as exc:
            return self._error_response(str(exc), status=400)
        except Exception as exc:
            return self._error_response('An error occurred while processing your request', status=500, details=str(exc))

    # @http.route('/api/inspections', type='http', auth='none', methods=['GET'], csrf=False, cors='*')
    # def list_inspections(self, **params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     domain = []
    #     state = params.get('state')
    #     if state:
    #         domain.append(('state', '=', state))
    #     date_from = params.get('date_from')
    #     if date_from:
    #         domain.append(('inspection_date', '>=', date_from))
    #     date_to = params.get('date_to')
    #     if date_to:
    #         domain.append(('inspection_date', '<=', date_to))

    #     limit = self._parse_int(params.get('limit', 50), 50)
    #     offset = self._parse_int(params.get('offset', 0), 0)

    #     inspections = request.env['ecis.inspection'].sudo().search(domain, limit=limit, offset=offset)
    #     return self._json_response({
    #         'success': True,
    #         'data': [self._serialize_inspection(r) for r in inspections],
    #         'count': len(inspections),
    #     })

    # @http.route('/api/inspections', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    # def create_inspection(self, **_params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     data = self._get_payload()
    #     equipment_id = data.get('equipment_id')
    #     if not equipment_id:
    #         return self._error_response('equipment_id is required', status=400)

    #     equipment = request.env['ecis.equipment'].sudo().browse(int(equipment_id))
    #     if not equipment.exists():
    #         return self._error_response('Equipment not found', status=404)

    #     inspector_id = self._get_inspector_user_id()
    #     if not inspector_id:
    #         return self._error_response('No inspector user available for inspection.', status=400)

    #     inspection_env = self._company_env('ecis.inspection')
    #     vals = {
    #         'equipment_id': equipment.id,
    #         'inspection_type': data.get('inspection_type') or 'periodic',
    #         'inspection_date': data.get('inspection_date') or fields.Date.today(),
    #         'inspection_duration': data.get('inspection_duration'),
    #         'weather_conditions': data.get('weather_conditions'),
    #         'overall_result': data.get('overall_result'),
    #         'defects_found': data.get('defects_found'),
    #         'immediate_actions_required': data.get('immediate_actions_required'),
    #         'recommendations': data.get('recommendations'),
    #         'inspector_notes': data.get('inspector_notes'),
    #         'next_inspection_due': data.get('next_inspection_due'),
    #         'next_inspection_frequency': data.get('next_inspection_frequency'),
    #         'inspector_id': inspector_id,
    #         'company_id': self._get_company_required().id,
    #     }
    #     inspection = inspection_env.create(vals)

    #     return self._json_response({
    #         'success': True,
    #         'data': self._serialize_inspection(inspection, include_checklist=True),
    #     }, status=201)

    # @http.route('/api/inspections/<int:inspection_id>', type='http', auth='none', methods=['GET'], csrf=False, cors='*')
    # def get_inspection(self, inspection_id, **params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     record = request.env['ecis.inspection'].sudo().browse(inspection_id)
    #     if not record.exists():
    #         return self._error_response('Not found', status=404)

    #     include_checklist = self._parse_bool(params.get('include_checklist'))
    #     return self._json_response({
    #         'success': True,
    #         'data': self._serialize_inspection(record, include_checklist=include_checklist),
    #     })

    # @http.route('/api/inspections/<int:inspection_id>', type='http', auth='none', methods=['PUT', 'PATCH'], csrf=False, cors='*')
    # def update_inspection(self, inspection_id, **_params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     record = request.env['ecis.inspection'].sudo().browse(inspection_id)
    #     if not record.exists():
    #         return self._error_response('Not found', status=404)

    #     data = self._get_payload()
    #     allowed_fields = {
    #         'inspection_type',
    #         'inspection_date',
    #         'inspection_duration',
    #         'weather_conditions',
    #         'overall_result',
    #         'defects_found',
    #         'immediate_actions_required',
    #         'recommendations',
    #         'inspector_notes',
    #         'next_inspection_due',
    #         'next_inspection_frequency',
    #         'state',
    #     }
    #     vals = {field: data.get(field) for field in allowed_fields if field in data}
    #     if vals:
    #         record.write(vals)

    #     return self._json_response({'success': True, 'data': self._serialize_inspection(record, include_checklist=True)})

    # @http.route('/api/inspections/<int:inspection_id>/start', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    # def start_inspection(self, inspection_id, **_params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     record = request.env['ecis.inspection'].sudo().browse(inspection_id)
    #     if not record.exists():
    #         return self._error_response('Not found', status=404)

    #     record.action_start_inspection()
    #     return self._json_response({'success': True, 'data': self._serialize_inspection(record)})

    # @http.route('/api/inspections/<int:inspection_id>/complete', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    # def complete_inspection(self, inspection_id, **_params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     record = request.env['ecis.inspection'].sudo().browse(inspection_id)
    #     if not record.exists():
    #         return self._error_response('Not found', status=404)

    #     try:
    #         record.action_complete_inspection()
    #     except UserError as exc:
    #         return self._error_response(str(exc), status=400)

    #     return self._json_response({'success': True, 'data': self._serialize_inspection(record)})

    # @http.route('/api/inspections/<int:inspection_id>/send', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    # def send_inspection(self, inspection_id, **_params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     record = request.env['ecis.inspection'].sudo().browse(inspection_id)
    #     if not record.exists():
    #         return self._error_response('Not found', status=404)

    #     result = record.action_send_to_client()
    #     return self._json_response({
    #         'success': True,
    #         'data': self._serialize_inspection(record),
    #         'notification': result if isinstance(result, dict) else None,
    #     })

    # @http.route('/api/inspections/<int:inspection_id>/cancel', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    # def cancel_inspection(self, inspection_id, **_params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     record = request.env['ecis.inspection'].sudo().browse(inspection_id)
    #     if not record.exists():
    #         return self._error_response('Not found', status=404)

    #     record.action_cancel()
    #     return self._json_response({'success': True, 'data': self._serialize_inspection(record)})

    # @http.route('/api/inspections/<int:inspection_id>/reset', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    # def reset_inspection(self, inspection_id, **_params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     record = request.env['ecis.inspection'].sudo().browse(inspection_id)
    #     if not record.exists():
    #         return self._error_response('Not found', status=404)

    #     record.action_reset_to_draft()
    #     return self._json_response({'success': True, 'data': self._serialize_inspection(record)})

    # @http.route('/api/inspections/<int:inspection_id>/report', type='http', auth='none', methods=['GET'], csrf=False, cors='*')
    # def inspection_report(self, inspection_id, **_params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     record = request.env['ecis.inspection'].sudo().browse(inspection_id)
    #     if not record.exists():
    #         return self._error_response('Not found', status=404)

    #     report = request.env.ref('ecis_inspection.action_report_inspection').sudo()
    #     pdf_content, _ = report._render_qweb_pdf(res_ids=[record.id])
    #     return self._json_response({
    #         'success': True,
    #         'data': {
    #             'filename': record.report_pdf_name or 'Inspection_Report.pdf',
    #             'content_base64': base64.b64encode(pdf_content).decode('ascii'),
    #         },
    #     })

    # @http.route('/api/inspections/<int:inspection_id>/checklist', type='http', auth='none', methods=['GET'], csrf=False, cors='*')
    # def list_checklist(self, inspection_id, **_params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     record = request.env['ecis.inspection'].sudo().browse(inspection_id)
    #     if not record.exists():
    #         return self._error_response('Inspection not found', status=404)

    #     items = [self._serialize_checklist_item(i) for i in record.checklist_ids]
    #     return self._json_response({'success': True, 'data': items})

    # @http.route('/api/inspections/<int:inspection_id>/checklist', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    # def create_checklist_item(self, inspection_id, **_params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     record = request.env['ecis.inspection'].sudo().browse(inspection_id)
    #     if not record.exists():
    #         return self._error_response('Inspection not found', status=404)

    #     data = self._get_payload()
    #     if not data.get('name'):
    #         return self._error_response('name is required', status=400)

    #     item = request.env['ecis.inspection.checklist'].sudo().create({
    #         'inspection_id': record.id,
    #         'sequence': self._parse_int(data.get('sequence', 10), 10),
    #         'name': data.get('name'),
    #         'requirement': data.get('requirement'),
    #         'status': data.get('status') or 'pass',
    #         'notes': data.get('notes'),
    #     })

    #     return self._json_response({'success': True, 'data': self._serialize_checklist_item(item)}, status=201)

    # @http.route('/api/checklist/<int:item_id>', type='http', auth='none', methods=['PUT', 'PATCH'], csrf=False, cors='*')
    # def update_checklist_item(self, item_id, **_params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     item = request.env['ecis.inspection.checklist'].sudo().browse(item_id)
    #     if not item.exists():
    #         return self._error_response('Checklist item not found', status=404)

    #     data = self._get_payload()
    #     allowed_fields = {'sequence', 'name', 'requirement', 'status', 'notes'}
    #     vals = {field: data.get(field) for field in allowed_fields if field in data}
    #     if vals:
    #         item.write(vals)

    #     return self._json_response({'success': True, 'data': self._serialize_checklist_item(item)})

    # @http.route('/api/checklist/<int:item_id>', type='http', auth='none', methods=['DELETE'], csrf=False, cors='*')
    # def delete_checklist_item(self, item_id, **_params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     item = request.env['ecis.inspection.checklist'].sudo().browse(item_id)
    #     if not item.exists():
    #         return self._error_response('Checklist item not found', status=404)

    #     item.unlink()
    #     return self._json_response({'success': True})

    # @http.route('/api/equipment', type='http', auth='none', methods=['GET'], csrf=False, cors='*')
    # def list_equipment(self, **params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     limit = self._parse_int(params.get('limit', 50), 50)
    #     offset = self._parse_int(params.get('offset', 0), 0)

    #     records = request.env['ecis.equipment'].sudo().search([], limit=limit, offset=offset)
    #     return self._json_response({
    #         'success': True,
    #         'data': [self._serialize_equipment(r) for r in records],
    #         'count': len(records),
    #     })

    # @http.route('/api/equipment', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    # def create_equipment(self, **_params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     data = self._get_payload()
    #     required = ['name', 'equipment_type', 'client_id']
    #     missing = [f for f in required if not data.get(f)]
    #     if missing:
    #         return self._error_response(f'Missing required fields: {", ".join(missing)}', status=400)

    #     client = request.env['res.partner'].sudo().browse(int(data.get('client_id')))
    #     if not client.exists():
    #         return self._error_response('Client not found', status=404)

    #     try:
    #         equipment_env = self._company_env('ecis.equipment')
    #         company_id = self._get_company_required().id
    #     except ValidationError as exc:
    #         return self._error_response(str(exc), status=400)

    #     equipment = equipment_env.create({
    #         'name': data.get('name'),
    #         'equipment_type': data.get('equipment_type'),
    #         'client_id': client.id,
    #         'company_id': company_id,
    #         'brand': data.get('brand'),
    #         'model': data.get('model'),
    #         'serial_number': data.get('serial_number'),
    #         'manufacture_year': data.get('manufacture_year'),
    #         'capacity': data.get('capacity'),
    #         'location': data.get('location'),
    #         'notes': data.get('notes'),
    #     })

    #     return self._json_response({'success': True, 'data': self._serialize_equipment(equipment)}, status=201)

    # @http.route('/api/equipment/<int:equipment_id>', type='http', auth='none', methods=['GET'], csrf=False, cors='*')
    # def get_equipment(self, equipment_id, **_params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     record = request.env['ecis.equipment'].sudo().browse(equipment_id)
    #     if not record.exists():
    #         return self._error_response('Not found', status=404)

    #     return self._json_response({'success': True, 'data': self._serialize_equipment(record)})

    # @http.route('/api/equipment/<int:equipment_id>/schedule-inspection', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    # def schedule_inspection(self, equipment_id, **_params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     equipment = request.env['ecis.equipment'].sudo().browse(equipment_id)
    #     if not equipment.exists():
    #         return self._error_response('Equipment not found', status=404)

    #     data = self._get_payload()
    #     inspection_env = self._company_env('ecis.inspection')
    #     inspector_id = self._get_inspector_user_id()
    #     if not inspector_id:
    #         return self._error_response('No inspector user available for inspection.', status=400)

    #     inspection = inspection_env.create({
    #         'equipment_id': equipment.id,
    #         'inspection_type': data.get('inspection_type') or 'periodic',
    #         'inspection_date': data.get('inspection_date') or fields.Date.today(),
    #         'inspection_duration': data.get('inspection_duration'),
    #         'weather_conditions': data.get('weather_conditions'),
    #         'inspector_notes': data.get('inspector_notes'),
    #         'inspector_id': inspector_id,
    #         'company_id': inspection_env.env.company.id,
    #     })

    #     return self._json_response({'success': True, 'data': self._serialize_inspection(inspection)}, status=201)

    # @http.route('/api/quote-requests', type='http', auth='none', methods=['GET'], csrf=False, cors='*')
    # def list_quote_requests(self, **params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     limit = self._parse_int(params.get('limit', 50), 50)
    #     offset = self._parse_int(params.get('offset', 0), 0)

    #     records = request.env['ecis.quote.request'].sudo().search([], limit=limit, offset=offset)
    #     return self._json_response({
    #         'success': True,
    #         'data': [self._serialize_quote_request(r) for r in records],
    #         'count': len(records),
    #     })

    # @http.route('/api/quote-requests/<int:request_id>', type='http', auth='none', methods=['GET'], csrf=False, cors='*')
    # def get_quote_request(self, request_id, **_params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     record = request.env['ecis.quote.request'].sudo().browse(request_id)
    #     if not record.exists():
    #         return self._error_response('Not found', status=404)

    #     return self._json_response({'success': True, 'data': self._serialize_quote_request(record)})

    # @http.route('/api/quote-requests/<int:request_id>/contact', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    # def contact_quote_request(self, request_id, **_params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     record = request.env['ecis.quote.request'].sudo().browse(request_id)
    #     if not record.exists():
    #         return self._error_response('Not found', status=404)

    #     record.action_contact_client()
    #     return self._json_response({'success': True, 'data': self._serialize_quote_request(record)})

    # @http.route('/api/quote-requests/<int:request_id>/send-quote', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    # def send_quote_request(self, request_id, **_params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     record = request.env['ecis.quote.request'].sudo().browse(request_id)
    #     if not record.exists():
    #         return self._error_response('Not found', status=404)

    #     record.action_send_quote()
    #     return self._json_response({'success': True, 'data': self._serialize_quote_request(record)})

    # @http.route('/api/quote-requests/<int:request_id>/convert', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    # def convert_quote_request(self, request_id, **_params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     record = request.env['ecis.quote.request'].sudo().browse(request_id)
    #     if not record.exists():
    #         return self._error_response('Not found', status=404)

    #     record.action_convert_to_client()
    #     return self._json_response({'success': True, 'data': self._serialize_quote_request(record)})

    # @http.route('/api/quote-requests/<int:request_id>/lost', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    # def lost_quote_request(self, request_id, **_params):
    #     auth_error = self._require_api_key()
    #     if auth_error:
    #         return auth_error

    #     record = request.env['ecis.quote.request'].sudo().browse(request_id)
    #     if not record.exists():
    #         return self._error_response('Not found', status=404)

    #     record.action_mark_lost()
    #     return self._json_response({'success': True, 'data': self._serialize_quote_request(record)})
