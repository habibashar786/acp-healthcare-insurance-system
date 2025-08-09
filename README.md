# ACP Healthcare Insurance System

Production-ready healthcare insurance management platform with FastAPI.

## Quick Deploy

### Railway (Recommended)
1. Fork this repository
2. Go to Railway.app
3. Click "Deploy from GitHub"
4. Select this repository
5. Automatic deployment!

### Render
1. Go to Render.com
2. New -> Web Service
3. Connect your GitHub repo
4. Automatic deployment from render.yaml!

### Heroku
```bash
heroku create acp-healthcare-system
git push heroku main
```

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main_system.py

# Access the API
http://localhost:8001

# API Documentation
http://localhost:8001/api/docs
```

## Testing

```bash
# Run tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

## Default Admin Account

- **Username**: admin
- **Password**: Admin@123456
- **Email**: admin@acp-health.com

WARNING: Change the default admin password in production!

## System Features

- **User Management**: Registration, authentication, role-based access
- **Insurance Plans**: Create and manage insurance plans
- **Policy Management**: Policy creation, activation, tracking
- **Claims Processing**: Submit and review insurance claims
- **Payment Tracking**: Payment history and management
- **Admin Dashboard**: Comprehensive admin controls
- **API Documentation**: Auto-generated Swagger/OpenAPI docs

## Security Features

- JWT Authentication
- Password hashing (bcrypt)
- Input validation with Pydantic
- SQL injection protection
- CORS configuration
- Role-based access control (Admin, Agent, Customer, Provider)

## API Endpoints

- **Health**: /health, /
- **Auth**: /register, /token, /me
- **Plans**: /plans (CRUD operations)
- **Policies**: /policies (CRUD operations)
- **Claims**: /claims (CRUD operations)
- **Payments**: /payments (CRUD operations)
- **Admin**: /admin/* (Admin operations)
- **Reports**: /reports/* (Analytics and reporting)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| SECRET_KEY | JWT secret key | Auto-generated |
| DATABASE_URL | Database connection | SQLite (local) |
| DEBUG | Debug mode | False |
| PORT | Application port | 8001 |

## Technology Stack

- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM
- **Pydantic**: Data validation
- **JWT**: Authentication
- **SQLite/PostgreSQL**: Database options
- **Pytest**: Testing framework

## Production Features

- Health monitoring endpoints
- Comprehensive error handling
- Structured logging
- Database relationship management
- API versioning support
- Security best practices

## API Documentation

Once the application is running, visit:
- **Swagger UI**: http://localhost:8001/api/docs
- **ReDoc**: http://localhost:8001/api/redoc

## License

MIT License - Open source healthcare management solution.

---

Built for healthcare insurance management with modern Python technologies.
