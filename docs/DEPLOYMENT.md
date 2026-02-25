# Deployment Guide

This guide covers deploying AI Council Coliseum to various environments.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Production Deployment](#production-deployment)
5. [Environment Variables](#environment-variables)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software
- Docker 24.0+ and Docker Compose 2.0+
- Python 3.11+ (for local development)
- Node.js 20+ (for local development)
- PostgreSQL 15+ (if not using Docker)
- Redis 7+ (if not using Docker)

### Required Accounts
- OpenAI API key (for AI agents)
- Anthropic API key (optional, for Claude)
- Solana RPC endpoint
- Ethereum RPC endpoint (Infura/Alchemy)
- Chainlink VRF subscription
- ElevenLabs API key (for TTS)

## Local Development

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (dev/test superset for local work)
pip install -r requirements-test.txt
# Runtime-only installs should use requirements.txt

# Setup environment
cp ../.env.example .env
# Edit .env with your configuration

# Run database migrations (when implemented)
# alembic upgrade head

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at `http://localhost:8000`  
API documentation at `http://localhost:8000/docs`

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
corepack enable
pnpm install

# Setup environment
cp ../.env.example .env.local
# Edit .env.local with your configuration

# Start development server
pnpm run dev
```

Frontend will be available at `http://localhost:3000`

## Docker Deployment

### Quick Start

```bash
# Clone repository
git clone https://github.com/ivviiviivvi/a-i-council--coliseum.git
cd a-i-council--coliseum

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Service Access

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Docker Commands

```bash
# Rebuild specific service
docker-compose build backend

# Restart specific service
docker-compose restart backend

# View service logs
docker-compose logs -f backend

# Execute command in container
docker-compose exec backend python -c "print('Hello')"

# Scale services (if configured)
docker-compose up -d --scale backend=3
```

## Production Deployment

### Using Docker on Cloud Providers

#### AWS Deployment

```bash
# Install AWS CLI and configure
aws configure

# Create ECR repositories
aws ecr create-repository --repository-name ai-council-backend
aws ecr create-repository --repository-name ai-council-frontend

# Build and push images
docker build -t ai-council-backend ./backend
docker tag ai-council-backend:latest \
  YOUR_AWS_ACCOUNT.dkr.ecr.REGION.amazonaws.com/ai-council-backend:latest
docker push YOUR_AWS_ACCOUNT.dkr.ecr.REGION.amazonaws.com/ai-council-backend:latest

# Deploy with ECS/EKS or EC2
# Follow AWS documentation for your chosen service
```

#### DigitalOcean Deployment

```bash
# Install doctl CLI
# Create App Platform app via UI or CLI

# Link repository
doctl apps create --spec .do/app.yaml

# Or use Docker deployment
doctl compute droplet create ai-council \
  --image docker-20-04 \
  --size s-2vcpu-4gb \
  --region nyc1

# SSH and setup
ssh root@droplet-ip
git clone YOUR_REPO
cd a-i-council--coliseum
docker-compose up -d
```

### Kubernetes Deployment

```bash
# Create namespace
kubectl create namespace ai-council

# Create secrets
kubectl create secret generic ai-council-secrets \
  --from-env-file=.env \
  --namespace=ai-council

# Apply configurations
kubectl apply -f k8s/ --namespace=ai-council

# Check status
kubectl get pods -n ai-council

# View logs
kubectl logs -f deployment/backend -n ai-council
```

### Database Setup

#### PostgreSQL Production Setup

```bash
# Using managed service (recommended)
# - AWS RDS
# - DigitalOcean Managed Database
# - Google Cloud SQL

# Or self-hosted:
# Install PostgreSQL
sudo apt-get install postgresql-15

# Create database and user
sudo -u postgres psql
CREATE DATABASE ai_council;
CREATE USER council_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE ai_council TO council_user;

# Configure connection string in .env
DATABASE_URL=postgresql://council_user:password@host:5432/ai_council
```

#### Redis Production Setup

```bash
# Using managed service (recommended)
# - AWS ElastiCache
# - Redis Cloud
# - DigitalOcean Managed Redis

# Or self-hosted:
sudo apt-get install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf
# Set password: requirepass your_secure_password

# Restart Redis
sudo systemctl restart redis-server

# Configure connection string in .env
REDIS_URL=redis://:password@host:6379
```

## Environment Variables

### Required Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379

# API Configuration
API_PORT=8000
API_HOST=0.0.0.0
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# AI Services
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Blockchain
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/YOUR_PROJECT_ID
CHAINLINK_VRF_COORDINATOR=0x...
CHAINLINK_SUBSCRIPTION_ID=123
CHAINLINK_KEY_HASH=0x...

# TTS
ELEVENLABS_API_KEY=your_key_here

# Frontend
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com
```

### Optional Variables

```bash
# Monitoring
SENTRY_DSN=https://...
PROMETHEUS_ENABLED=true

# Features
ENABLE_RATE_LIMITING=true
MAX_REQUESTS_PER_MINUTE=100
```

## SSL/TLS Configuration

### Using Let's Encrypt with Nginx

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Check all services
docker-compose ps
```

### Logs

```bash
# Docker logs
docker-compose logs -f --tail=100

# System logs (if not using Docker)
journalctl -u ai-council-backend -f
journalctl -u ai-council-frontend -f
```

### Metrics

```bash
# Prometheus metrics (if enabled)
curl http://localhost:8000/metrics

# Application stats
curl http://localhost:8000/api/stats
```

## Backup and Recovery

### Database Backup

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U council_user ai_council > backup.sql

# Or for production:
pg_dump -h host -U user -d dbname > backup.sql

# Restore
docker-compose exec -T postgres psql -U council_user ai_council < backup.sql
```

### Redis Backup

```bash
# Redis automatically saves to dump.rdb
# Copy the file for backup
docker-compose exec redis redis-cli SAVE
docker cp ai-council-redis:/data/dump.rdb ./backup-redis.rdb
```

## Scaling

### Horizontal Scaling

```bash
# Scale backend instances
docker-compose up -d --scale backend=3

# Use load balancer (Nginx/HAProxy)
# Update nginx.conf with upstream configuration
```

### Database Scaling

- Use read replicas for read-heavy workloads
- Implement connection pooling (pgBouncer)
- Cache frequently accessed data in Redis

## Security Checklist

- [ ] Change all default passwords
- [ ] Use strong secret keys
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Enable rate limiting
- [ ] Set up regular backups
- [ ] Update dependencies regularly
- [ ] Monitor security advisories
- [ ] Enable audit logging
- [ ] Implement fail2ban for SSH

## Troubleshooting

### Common Issues

**Issue: Backend won't start**
```bash
# Check logs
docker-compose logs backend

# Verify environment variables
docker-compose config

# Check database connection
docker-compose exec backend python -c "from sqlalchemy import create_engine; engine = create_engine('your_db_url'); engine.connect()"
```

**Issue: Frontend build fails**
```bash
# Clear cache
rm -rf frontend/node_modules frontend/.next
cd frontend && pnpm install && pnpm run build

# Check Node version
node --version  # Should be 20+
```

**Issue: Database connection errors**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U council_user -d ai_council

# Verify connection string in .env
```

**Issue: Redis connection errors**
```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping

# Should return PONG
```

### Performance Issues

```bash
# Monitor resource usage
docker stats

# Check database slow queries
docker-compose exec postgres psql -U council_user -d ai_council \
  -c "SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Monitor Redis memory
docker-compose exec redis redis-cli INFO memory
```

## Support

For additional help:
- GitHub Issues: https://github.com/ivviiviivvi/a-i-council--coliseum/issues
- Documentation: /docs
- Community Discussions: GitHub Discussions

## Updates and Maintenance

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose build

# Restart services
docker-compose down
docker-compose up -d

# Run migrations (when implemented)
docker-compose exec backend alembic upgrade head
```

---

For more detailed information, see:
- [Architecture Documentation](ARCHITECTURE.md)
- [Contributing Guide](../CONTRIBUTING.md)
- [README](../README.md)
