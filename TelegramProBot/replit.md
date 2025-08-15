# Chess Bot Project

## Overview

This is a comprehensive Telegram chess bot application built with Flask and Python. The bot allows users to play chess games against the Stockfish engine through Telegram's chat interface with modern button-based interactions. The system includes a complete web-based administration panel for monitoring users, games, and system performance in real-time.

Key features include:
- Interactive chess gameplay with French localization
- Modern button-based interface (no text commands)
- Real-time admin monitoring dashboard
- User management and game tracking
- Board rendering to PNG images
- Export functionality (PNG, FEN, PGN)
- Multi-user support with session isolation

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Structure
The application follows a modular Flask architecture with clear separation of concerns:
- **app.py** - Main Flask application factory with SQLAlchemy and SocketIO setup
- **bot.py** - Telegram bot implementation using python-telegram-bot library
- **models.py** - SQLAlchemy database models for users, games, and activities
- **routes.py** - Web application routes and API endpoints
- **admin_routes.py** - Administrative interface routes with authentication

### Chess Engine Integration
The chess functionality is built around the python-chess library with Stockfish integration:
- **chess_engine.py** - Chess game logic and AI move generation
- **board_renderer.py** - Chess board visualization using SVG to PNG conversion
- Uses cairosvg for rendering chess boards as images

### Real-time Features
Real-time monitoring is implemented using Flask-SocketIO:
- **real_time_monitor.py** - WebSocket handlers for live dashboard updates
- **static/js/realtime.js** - Client-side JavaScript for real-time data visualization
- Live activity streams and performance metrics

### Authentication & Security
- Flask-Login for session management
- Admin user model with password hashing
- Owner-based permissions for administrative functions
- User activity tracking and monitoring

### Database Architecture
SQLAlchemy models with relationships:
- **AdminUser** - Administrative users with login capabilities
- **TelegramUser** - Bot users with Telegram integration
- **ChessGame** - Game state storage with FEN notation
- **UserActivity** - Activity logging and analytics
- **GameMove** and **SystemStats** - Additional tracking models

### Frontend Architecture
Bootstrap-based admin interface with:
- Responsive dashboard design
- Real-time charts and monitoring
- User and game management interfaces
- French localization throughout

## External Dependencies

### Core Framework Dependencies
- **Flask** - Web application framework
- **SQLAlchemy** - Database ORM and migrations
- **Flask-Login** - User session management
- **Flask-SocketIO** - Real-time WebSocket communication

### Chess Engine Dependencies
- **python-chess** - Chess game logic and move validation
- **Stockfish** - Chess engine for AI opponent (external binary)
- **cairosvg** - SVG to PNG conversion for board rendering

### Telegram Integration
- **python-telegram-bot** - Telegram Bot API wrapper
- Webhook-based message handling for production deployment

### Frontend Dependencies
- **Bootstrap 5** - UI framework and responsive design
- **Font Awesome** - Icon library
- **Chart.js** - Real-time data visualization (referenced in templates)

### Development & Deployment
- **Railway** - Cloud hosting platform (environment variables configured)
- **Replit** - Development environment support
- **Werkzeug** - WSGI utilities and development server

### Database Support
- **SQLite** - Default development database
- **PostgreSQL** - Production database support via DATABASE_URL
- Connection pooling and health checks configured

Note: The application is designed to work with various database backends through SQLAlchemy, with SQLite as the default for development and PostgreSQL support for production deployments.