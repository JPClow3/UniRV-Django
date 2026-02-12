#!/bin/bash
# ============================================
# Environment Setup Script
# ============================================
# Quickly sets up .env file for your environment
#
# Usage:
#   bash setup_env.sh
#   # or
#   ./setup_env.sh

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}AgroHub Environment Setup${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if .env already exists
if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file already exists!${NC}"
    read -p "Do you want to overwrite it? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 1
    fi
fi

# Ask which environment
echo -e "${BLUE}Which environment are you setting up?${NC}"
echo "1) Development (local, with console emails)"
echo "2) Docker (production-ready, for Docker/staging/production)"
echo "3) Custom (.env.example - manually edit)"
read -p "Select environment (1-3): " env_choice

case $env_choice in
    1)
        ENV_FILE=".env.development"
        ENV_NAME="Development"
        ;;
    2)
        ENV_FILE=".env.docker.example"
        ENV_NAME="Docker"
        ;;
    3)
        ENV_FILE=".env.example"
        ENV_NAME="Custom"
        ;;
    *)
        echo -e "${RED}Invalid choice.${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✓ Setting up ${ENV_NAME} environment${NC}"

# Copy environment file
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: $ENV_FILE not found!${NC}"
    exit 1
fi

cp "$ENV_FILE" .env
echo -e "${GREEN}✓ Copied $ENV_FILE to .env${NC}"

# For production/Docker/custom, offer to generate SECRET_KEY
if [ "$env_choice" != "1" ]; then
    echo ""
    echo -e "${BLUE}Do you want to generate a new SECRET_KEY?${NC}"
    read -p "Generate SECRET_KEY? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
        
        # Replace SECRET_KEY in .env (works on both macOS and Linux)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/^SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
        else
            # Linux
            sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
        fi
        
        echo -e "${GREEN}✓ Generated and set SECRET_KEY${NC}"
    fi
fi

# Show next steps
echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✓ Environment setup complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""

case $env_choice in
    1)
        echo "1. Review .env file and adjust if needed:"
        echo "   nano .env"
        echo ""
        echo "2. Start database and Redis:"
        echo "   docker-compose up -d db redis"
        echo ""
        echo "3. Run migrations:"
        echo "   python manage.py migrate"
        echo ""
        echo "4. Create admin user (optional):"
        echo "   python manage.py createsuperuser"
        echo ""
        echo "5. Start development server:"
        echo "   python manage.py runserver"
        echo ""
        echo "6. Visit http://localhost:8000"
        ;;
    2)
        echo "1. Edit .env with your actual credentials:"
        echo "   nano .env"
        echo ""
        echo "2. Key fields to update:"
        echo "   - SECRET_KEY (generate: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
        echo "   - ALLOWED_HOSTS (your domain)"
        echo "   - DB_PASSWORD (secure password)"
        echo "   - Database connection (db:5432 for Docker)"
        echo "   - Email configuration (MailerSend, SMTP, etc.)"
        echo ""
        echo "3. Start Docker:"
        echo "   docker-compose up --build -d"
        echo ""
        echo "4. Visit http://localhost:8000 or your domain"
        ;;
    3)
        echo "1. Edit .env.example with your values:"
        echo "   nano .env"
        echo ""
        echo "2. Configure based on your needs:"
        echo "   - See .env.example for all available variables"
        echo "   - See ENVIRONMENT_SETUP.md for documentation"
        echo "   - Choose appropriate settings for your environment"
        echo ""
        echo "3. Run migrations and deploy based on your setup"
        ;;
esac

echo ""
echo -e "${BLUE}ℹ️  Documentation:${NC}"
echo "   - Read ENV_SETUP.md for detailed guide"
echo "   - Read ENV_QUICK_REFERENCE.md for comparison"
echo "   - Check .env.example for all available variables"
echo ""

