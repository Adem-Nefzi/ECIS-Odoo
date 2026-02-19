# ECIS Inspection Management System

A comprehensive Odoo-based inspection management solution with professional PDF report generation, customizable checklists, and a modern white-label interface.

## Overview

ECIS (Equipment Certification & Inspection System) is an enterprise-grade inspection management platform built on Odoo 17.0. It provides organizations with tools to manage equipment inspections, generate professional reports, handle certifications, and maintain detailed inspection histories all within a modern, scalable architecture.

**Developed by:** NefziAdem + SouilhiLouey - ECIS-DZ

## Features

### Core Inspection Management

- **Equipment Registration** - Register and manage equipment with detailed specifications
- **Inspection Scheduling** - Calendar-based inspection scheduling and management
- **Customizable Checklists** - Create and manage reusable inspection checklists
- **Inspection Reports** - Generate professional PDF inspection reports with signatures
- **Digital Signatures** - Support for digital signatures on inspection documents
- **Mail Templates** - Automated email notifications and communications

### Technical Features

- **RESTful API** - Complete REST API with CORS support for third-party integrations
- **White Label Support** - Customizable branding for the web interface
- **Portal Access** - User portal for inspection stakeholders
- **Security Controls** - Role-based access control with granular permissions
- **Document Management** - Integrated document handling with PDF generation

## Project Structure

```
ecis-odoo/
├── docker-compose.yml          # Docker Compose configuration
├── config/
│   └── odoo.conf              # Odoo configuration file
└── addons/
    ├── ecis_inspection/       # Main inspection module
    │   ├── controllers/       # API endpoints and web controllers
    │   ├── models/           # Data models (Equipment, Inspection, Checklist, Quote)
    │   ├── views/           # UI views and templates
    │   ├── reports/         # PDF report generation templates
    │   ├── data/            # Initial data (sequences, templates)
    │   ├── security/        # Access control rules
    │   └── __manifest__.py   # Module configuration
    └── ecis_white_label/     # Branding module
        ├── static/           # CSS, JavaScript, and images
        ├── views/           # Web client templates
        └── __manifest__.py   # Module configuration
```

## Prerequisites

- **Docker Desktop** (Windows/Mac) or Docker Engine (Linux)
- **Docker Compose** v1.29+
- **Python** 3.10+ (if running without Docker)
- **PostgreSQL** 15+ (if running without Docker)
- **Git** for version control

## Installation & Setup

### Option 1: Docker (Recommended)

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd ecis-odoo
   ```

2. **Start the services:**

   ```bash
   docker-compose up -d
   ```

3. **Access Odoo:**
   - Open your browser and navigate to `http://localhost:8069`
   - Default admin credentials will be set during initial setup

4. **Install modules:**
   - Go to Apps menu
   - Search for "ECIS Inspection Management" or "ECIS White Label"
   - Click "Install"

### Option 2: Manual Setup

1. **Install Odoo 17.0:**

   ```bash
   pip install odoo==17.0
   ```

2. **Set up PostgreSQL database:**

   ```bash
   createdb odoo_db
   ```

3. **Copy addons to Odoo addons path:**

   ```bash
   cp -r addons/* /path/to/odoo/addons/
   ```

4. **Update Odoo configuration:**

   ```bash
   # Edit your odoo.conf file
   addons_path = /path/to/addons,/usr/lib/python3/dist-packages/odoo/addons
   ```

5. **Start Odoo:**
   ```bash
   odoo --addons-path=/path/to/addons
   ```

## Modules

### 1. ECIS Inspection Management (v1.0.0)

**Category:** Services/Inspection

The core module providing complete inspection management functionality.

#### Data Models

- **Equipment** - Equipment registry with specifications and status tracking
- **Inspection** - Inspection records with detailed findings
- **Checklist** - Reusable inspection checklist templates
- **Quote Request** - Quote management for inspection services

#### Key Features

- Equipment lifecycle management
- Inspection scheduling and execution
- Professional PDF report generation
- Digital signature support
- Email notifications via Jinja2 templates
- Sequence-based numbering for documents

#### Dependencies

- base (Odoo core)
- mail (Email functionality)
- contacts (Contact management)
- portal (Portal access)

#### Security

- Role-based access control (RBAC)
- Model-level access rules
- Field-level security constraints

### 2. ECIS White Label (v1.0.1)

**Category:** Tools

Provides branding customization for the Odoo web interface.

#### Features

- Custom CSS styling for web client
- Company branding integration
- UI/UX enhancements
- Asset pipeline integration

#### Customization

- Logo and color scheme customization
- Web client template overrides
- Responsive design adjustments

#### Dependencies

- web (Odoo web framework)

## API Documentation

The ECIS Inspection module provides a RESTful API for programmatic access and third-party integrations.

### API Features

- **CORS Support** - Cross-Origin Resource Sharing enabled
- **JSON Responses** - All endpoints return JSON format
- **Error Handling** - Comprehensive error messages with details
- **Date Serialization** - ISO 8601 format for all datetime fields
- **Binary Data** - Base64 encoding for file attachments

### API Endpoints

All API endpoints are prefixed with `/api/inspection/`

**Example endpoints:**

- `GET /api/inspection/equipment` - List equipment
- `POST /api/inspection/equipment` - Create equipment
- `GET /api/inspection/inspection/<id>` - Get inspection details
- `POST /api/inspection/inspection` - Create inspection
- `GET /api/inspection/checklist` - List checklists

### Request Format

```json
{
  "method": "POST",
  "endpoint": "/api/inspection/equipment",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer <token>"
  },
  "body": {
    "name": "Equipment Name",
    "serial_number": "SN12345",
    "equipment_type": "Type"
  }
}
```

### Response Format

**Success Response:**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Equipment Name",
    "created_at": "2024-01-15T10:30:00"
  }
}
```

**Error Response:**

```json
{
  "success": false,
  "error": "Error message",
  "details": {
    "field": "Specific error details"
  }
}
```

## Configuration

### Environment Variables (Docker)

The following environment variables can be set in `docker-compose.yml`:

```yaml
environment:
  - HOST=db # Database host
  - USER=odoo # Database user
  - PASSWORD=odoo_password # Database password
  - POSTGRES_DB=postgres # Database name
  - POSTGRES_USER=odoo
  - POSTGRES_PASSWORD=odoo_password
```

### Odoo Configuration (odoo.conf)

Key configuration options:

```ini
[options]
admin_passwd = $pbkdf2-sha512$...  # Admin password hash
addons_path = /mnt/extra-addons    # Addon directory paths
```

## Development

### Project Setup for Developers

1. **Clone and install development dependencies:**

   ```bash
   git clone <repository-url>
   cd ecis-odoo
   docker-compose up -d
   ```

2. **Enable development mode:**
   - The docker-compose configuration includes `--dev=all` flag
   - This enables Python debugging and automatic module reloading

3. **Access Odoo Developer Mode:**
   - Login to Odoo
   - Click your user menu (top-right)
   - Select "Developer Mode"

### Code Structure Guidelines

- **Models** (`models/`) - Define data structures and business logic
- **Controllers** (`controllers/`) - Handle HTTP requests and API endpoints
- **Views** (`views/`) - Define UI using XML templates
- **Reports** (`reports/`) - Generate PDF and documents
- **Data** (`data/`) - Initial data and fixtures
- **Security** (`security/`) - Access control rules and field restrictions

### Database Access

Connect to the development database:

```bash
docker-compose exec db psql -U odoo -d postgres
```

### Logs

View Odoo logs:

```bash
docker-compose logs -f web
```

## Building & Deployment

### Development Build

```bash
docker-compose up -d
```

### Production Build

For production deployment:

1. Set secure admin password in `odoo.conf`
2. Configure database backups
3. Enable security modules and access controls
4. Configure SSL/TLS certificates
5. Set up log rotation and monitoring
6. Use environment-specific configuration files

## Security

### Access Control

- All models have security rules defined in `security/ir.model.access.csv`
- Role-based access control (Sales, Manager, Admin roles)
- API endpoints validate user permissions

### Data Protection

- Sensitive data (signatures, reports) are stored securely
- Email templates use secure token-based authentication
- CORS headers restrict cross-origin access

### Best Practices

- Always use HTTPS in production
- Store sensitive configuration in environment variables
- Regularly backup the PostgreSQL database
- Keep Odoo and dependencies updated

## Troubleshooting

### Docker Issues

**Ports already in use:**

```bash
# Change port in docker-compose.yml or kill process
docker-compose down
# Or change mapping: "8069:8069" to "8070:8069"
```

**Database connection errors:**

```bash
docker-compose down -v  # Remove volumes
docker-compose up -d    # Recreate containers
```

### Odoo Issues

**Module not loading:**

- Check manifest.py for syntax errors
- Verify dependencies are installed
- Restart Odoo: `docker-compose restart web`

**Permissions errors:**

- Verify security rules in `ir.model.access.csv`
- Check role assignments in Odoo UI

**API errors:**

- Check browser console for CORS errors
- Verify API endpoint paths and HTTP methods
- Check authentication tokens

## Performance Optimization

### Database

- Use indexes on frequently queried fields
- Implement pagination for large datasets
- Monitor slow queries regularly

### Caching

- Enable Odoo session caching for better performance
- Use browser caching for static assets

## File Upload Support

The ECIS system supports file uploads for:

- Inspection documents
- Equipment photos
- PDF attachments
- Signature images

Maximum file size and supported formats can be configured in Odoo settings.

## Mail Integration

Automated email notifications are sent for:

- Inspection scheduling confirmations
- Report completion notifications
- Quote request updates
- System alerts

Configure email settings in Odoo: Settings > Email > Outgoing Mail Servers

## License

This project is licensed under LGPL-3. See the module manifests for detailed license information.

## Support & Contribution

### Reporting Issues

If you encounter any bugs or have feature requests, please:

1. Check existing issues in the repository
2. Provide detailed reproduction steps
3. Include relevant logs and screenshots

### Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## Author

**Nefzi Adem - ECIS-DZ**

For more information, visit: https://ecis-dz.com

## Changelog

### Version 1.0.0

- Initial release of ECIS Inspection Management System
- Complete equipment and inspection management
- PDF report generation with signatures
- RESTful API with CORS support
- White label branding module
- Email notification system

---

**Last Updated:** February 2026

For questions or support, please contact the development team.
