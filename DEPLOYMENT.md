# Deployment Guide - Claims AI Application

## Prehľad
Tento dokument obsahuje kompletné inštrukcie pre nasadenie Claims AI aplikácie externej firmou.

## Požiadavky na infraštruktúru

### Minimálne požiadavky
- **CPU**: 4 vCPU (Intel/AMD x64)
- **RAM**: 8GB
- **Storage**: 50GB SSD
- **OS**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **Network**: Outbound HTTPS prístup na Google Cloud APIs

### Odporúčané požiadavky
- **CPU**: 8 vCPU
- **RAM**: 16GB
- **Storage**: 100GB SSD
- **OS**: Ubuntu 22.04 LTS
- **Network**: Dedicated IP, SSL certifikát

## Príprava prostredia

### 1. Inštalácia Docker a Docker Compose
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Inštalácia Git
```bash
sudo apt update
sudo apt install git
```

## Nasadenie aplikácie

### 1. Klonovanie repozitára
```bash
git clone <repository-url>
cd google-cloud
```

### 2. Konfigurácia Google Cloud
1. Stiahnite service account JSON kľúč z GCP Console
2. Premenujte na `service-account-key.json`
3. Umiestnite do koreňového priečinka

### 3. Konfigurácia aplikácie
```bash
# Skopírujte env.example
cp env.example .env

# Upravte .env súbor s vašimi hodnotami
nano .env
```

### 4. Spustenie aplikácie
```bash
# Spustenie všetkých služieb
docker-compose up -d

# Kontrola stavu
docker-compose ps

# Logy
docker-compose logs -f claims_ai
```

## Konfigurácia databázy

### MySQL (predvolené)
- **Host**: localhost:3306
- **Database**: claims_ai
- **User**: claims_user
- **Password**: claims_password

### SQLite (alternatívne)
Ak nechcete MySQL, upravte `config.ini`:
```ini
[database]
url = sqlite:///claims_ai.db
```

## Monitoring a logy

### Health checks
- **Streamlit**: http://localhost:8501
- **FastAPI**: http://localhost:8000/health
- **Swagger**: http://localhost:8000/docs

### Logy
```bash
# Aplikácia
docker-compose logs claims_ai

# Databáza
docker-compose logs mysql

# Nginx
docker-compose logs nginx
```

## Bezpečnosť

### Firewall
```bash
# Povoliť len potrebné porty
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 8501  # Streamlit
sudo ufw allow 8000  # FastAPI
sudo ufw enable
```

### SSL/HTTPS
1. Získajte SSL certifikát (Let's Encrypt)
2. Nakonfigurujte Nginx
3. Presmerujte HTTP na HTTPS

## Backup a recovery

### Databáza
```bash
# Backup
docker-compose exec mysql mysqldump -u root -p claims_ai > backup.sql

# Restore
docker-compose exec -T mysql mysql -u root -p claims_ai < backup.sql
```

### Aplikácia
```bash
# Backup konfigurácie
tar -czf config-backup.tar.gz config.ini service-account-key.json

# Backup dát
tar -czf data-backup.tar.gz poistne_udalosti/ anonymized_output/ general_output/ raw_ocr_output/ analysis_output/
```

## Troubleshooting

### Časté problémy
1. **Port 8501/8000 už používané**
   - Zastavte existujúce služby
   - Skontrolujte `netstat -tulpn | grep :8501`

2. **Google Cloud autentifikácia**
   - Overte `service-account-key.json`
   - Skontrolujte `GOOGLE_APPLICATION_CREDENTIALS`

3. **Databáza nepripojí**
   - Skontrolujte MySQL stav: `docker-compose ps mysql`
   - Overte credentials v `.env`

### Support
Pre technickú podporu kontaktujte:
- Email: [vaša email adresa]
- Dokumentácia: [link na internú dokumentáciu]

## Produkčné nasadenie

### Load Balancer
- Nginx alebo HAProxy
- SSL termination
- Rate limiting

### Monitoring
- Prometheus + Grafana
- Alerting na kritické chyby
- Log aggregation (ELK stack)

### Scaling
- Horizontal scaling s Docker Swarm/Kubernetes
- Auto-scaling na základe CPU/RAM
- Database connection pooling
