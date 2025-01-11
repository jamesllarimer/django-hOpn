# Sports League Manager

A Django-based web application for managing sports leagues, team registrations, and player management.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- Python 3.x
- PostgreSQL 15
- Homebrew (for macOS users)

## Installation Steps

1. **Install PostgreSQL**
   ```bash
   # Using Homebrew
   brew install postgresql@15
   
   # Start PostgreSQL service
   brew services start postgresql@15
   ```

2. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd league-manager-app
   ```

3. **Create and activate virtual environment**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   
   # Activate virtual environment
   source venv/bin/activate  # On macOS/Linux
   # or
   .\venv\Scripts\activate  # On Windows
   ```

4. **Install dependencies**
   ```bash
   # Upgrade pip
   pip install --upgrade pip
   
   # Install requirements
   pip install -r requirements.txt
   ```

5. **Database Setup**
   ```bash
   # Create database
   createdb league_manager_db
   
   # Run migrations
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Environment Variables**
   Create a `.env` file in the root directory with the following variables:
   ```
   DEBUG=True
   SECRET_KEY=your-secret-key
   DATABASE_URL=postgres://localhost/league_manager_db
   TEST_STRIPE_SECRET_KEY=your-stripe-test-key
   ```

## Running the Application

1. **Start the development server**
   ```bash
   python manage.py runserver
   ```
   The application will be available at http://127.0.0.1:8000/

2. **Access the admin interface**
   - Go to http://127.0.0.1:8000/admin
   - Log in with your superuser credentials

## Key Features

- User authentication and registration
- League and team management
- Player registration system
- Free agent pool
- Team captain functionality
- Stripe payment integration
- Admin dashboard

## Common Issues and Solutions

1. **psycopg2 installation issues**
   ```bash
   brew install postgresql-connector-c
   pip install psycopg2-binary
   ```

2. **PostgreSQL connection issues**
   - Ensure PostgreSQL service is running:
     ```bash
     brew services start postgresql@15
     ```
   - Check database existence:
     ```bash
     psql -l  # List all databases
     ```

3. **Missing dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Project Structure

- `sportsSignUp/` - Main application directory
- `config/` - Project configuration files
- `templates/` - HTML templates
- `static/` - Static files (CSS, JavaScript, images)

## Development Tasks

1. **Create new migrations**
   ```bash
   python manage.py makemigrations
   ```

2. **Apply migrations**
   ```bash
   python manage.py migrate
   ```

3. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

4. **Collect static files**
   ```bash
   python manage.py collectstatic
   ```

## Testing

```bash
python manage.py test
```

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Run tests
4. Submit a pull request

## Support

For support and questions, please contact the development team or create an issue in the repository.
