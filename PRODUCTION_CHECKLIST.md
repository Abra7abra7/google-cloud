# Production Deployment Checklist

## Pre-nasadenie

### ✅ Infraštruktúra
- [ ] Server má minimálne 4 vCPU, 8GB RAM, 50GB SSD
- [ ] OS je Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- [ ] Docker a Docker Compose sú nainštalované
- [ ] Firewall je nakonfigurovaný (porty 22, 80, 443, 8502, 8000)
- [ ] SSL certifikát je pripravený (Let's Encrypt alebo komerčný)

### ✅ Google Cloud
- [ ] Service account JSON kľúč je stiahnutý
- [ ] Document AI API je povolené
- [ ] Cloud DLP API je povolené
- [ ] Vertex AI API je povolené
- [ ] DLP templates sú vytvorené
- [ ] Document AI processor je aktívny

### ✅ Aplikácia
- [ ] Repository je klonované
- [ ] Service account kľúč je umiestnený ako `service-account-key.json`
- [ ] `.env.local` je nakonfigurovaný (jediný zdroj pravdy)
- [ ] `config.ini` sa nepoužíva (archívny)
- [ ] Všetky Python závislosti sú nainštalované

## Nasadenie

### ✅ Docker
- [ ] `docker-compose up -d` je úspešné
- [ ] Všetky kontajnery bežia (`docker-compose ps`)
- [ ] Porty 8501 a 8000 sú dostupné
- [ ] Health checks prechádzajú

### ✅ Databáza
- [ ] MySQL kontajner beží
- [ ] Databáza `claims_ai` je vytvorená
- [ ] Tabuľky sú inicializované
- [ ] Connection string je správny

### ✅ Služby
- [ ] Streamlit beží na porte 8502
- [ ] FastAPI beží na porte 8000
- [ ] Swagger UI je dostupné na `/docs`
- [ ] Health endpoint `/health` vracia 200 OK

## Testovanie

### ✅ Funkčnosť
- [ ] Upload PDF funguje
- [ ] OCR spracovanie funguje
- [ ] Anonymizácia funguje
- [ ] AI analýza funguje
- [ ] Databáza ukladá dáta

### ✅ API
- [ ] Všetky endpointy vracajú správne HTTP kódy
- [ ] Error handling funguje
- [ ] Rate limiting je aktívny (ak je nakonfigurovaný)
- [ ] CORS je nakonfigurovaný (ak je potrebný)

### ✅ Bezpečnosť
- [ ] Service account má minimálne potrebné oprávnenia
- [ ] Databáza credentials sú bezpečné
- [ ] SSL/HTTPS je nakonfigurovaný
- [ ] Firewall blokuje nepotrebné porty

## Monitoring

### ✅ Logy
- [ ] Aplikácia loguje do súborov
- [ ] Log rotation je nakonfigurovaný
- [ ] Error logy sú zachytené
- [ ] Performance logy sú aktívne

### ✅ Metriky
- [ ] CPU a RAM usage sa sleduje
- [ ] Disk usage sa sleduje
- [ ] Network usage sa sleduje
- [ ] Database performance sa sleduje

### ✅ Alerting
- [ ] Kritické chyby spúšťajú notifikácie
- [ ] High resource usage spúšťa alerty
- [ ] Service downtime je detekovaný
- [ ] Backup failures sú hlásené

## Backup a Recovery

### ✅ Backup
- [ ] Database backup je automatický
- [ ] Application data backup je nakonfigurovaný
- [ ] Backup retention policy je definovaný
- [ ] Backup restore je otestovaný

### ✅ Disaster Recovery
- [ ] Recovery procedures sú dokumentované
- [ ] RTO a RPO sú definované
- [ ] Failover plan existuje
- [ ] Recovery testy sú vykonané

## Dokumentácia

### ✅ Pre tím
- [ ] README.md je aktuálny
- [ ] API dokumentácia je kompletná
- [ ] Deployment guide je pripravený
- [ ] Troubleshooting guide existuje

### ✅ Pre používateľov
- [ ] User manual je pripravený
- [ ] FAQ sekcia existuje
- [ ] Video tutoriály sú nahrané
- [ ] Support contact info je aktuálne

## Finalizácia

### ✅ Handover
- [ ] Všetky credentials sú predané
- [ ] Access control je nakonfigurovaný
- [ ] Support procedures sú definované
- [ ] Escalation matrix existuje

### ✅ Training
- [ ] Tím je vyškolený na používanie
- [ ] Admin procedures sú vysvetlené
- [ ] Monitoring tools sú demonštrované
- [ ] Troubleshooting je prakticky otestovaný

---

**Dátum kontroly**: _______________
**Kontroloval**: _______________
**Podpis**: _______________
