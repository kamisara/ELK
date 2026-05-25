```markdown
# ELK Stack — Centralized Observability Lab

A lab implementation for Systems Reliability Engineering (SRE) — Chapter 5.
This project demonstrates centralized log collection and analysis across three
distinct telemetry sources using the ELK Stack deployed via Docker Compose.

## Overview

This lab simulates a real-world observability pipeline for an e-commerce platform
experiencing intermittent checkout failures. Three data sources feed into a
centralized logging hub, enabling cross-source correlation and real-time analysis
in Kibana.

**Data Sources:**
- A containerized Python/Flask checkout microservice (Docker)
- An Nginx web server running on an Ubuntu edge node
- A Windows machine shipping Security Event logs

## Pipeline Architecture

```
[Checkout Microservice]
        |
   Filebeat (Docker container)
        |
        v
[Logstash :5044] <---- Filebeat (Ubuntu Nginx VM)
        |        <---- Winlogbeat (Windows Machine)
        v
[Elasticsearch]
        |
        v
   [Kibana :5601]
```

## Repository Layout

```
.
├── docker-compose.yml        # Spins up the full ELK hub + microservice
├── .env                      # Stack version and port configuration
├── logstash.conf             # Pipeline: input → grok/json filter → ES output
├── microservice/
│   ├── app.py                # Flask checkout app (success/timeout/payment_failed)
│   ├── DockerFile            # Container image definition
│   ├── filebeat.yml          # Reads Docker container logs, ships to Logstash
│   ├── generate_traffic.ps1  # PowerShell traffic simulator
│   └── requirements.txt      # Python dependencies (flask)
└── server conf files/
    ├── nginx/
    │   ├── filebeat.yml          # Filebeat config for Ubuntu Nginx VM
    │   └── sample_nginx.log      # Sample nginx access log for testing
    └── windows/
        ├── winlogbeat.yml        # Winlogbeat config for Windows security events
        └── sample_windows_events.txt  # Sample exported Windows event log
```

## Stack Components

| Container | Port | Role |
|---|---|---|
| elasticsearch | 9200 | Log storage and search engine |
| logstash | 5044 | Log processing and routing |
| kibana | 5601 | Visualization and dashboards |
| checkout-microservice | 5000 | Simulated e-commerce backend |
| filebeat | — | Docker log collector |

## Environment Configuration

All configurable parameters are stored in `.env`:

```env
STACK_VERSION=8.13.0
CLUSTER_NAME=elk-lab-cluster
ES_PORT=9200
KIBANA_PORT=5601
ES_MEM_LIMIT=512m
KIBANA_PASSWORD=changeme
ENCRYPTION_KEY=a_very_long_random_string_at_least_32chars
```

Security is intentionally disabled for this lab environment:

```yaml
xpack.security.enabled=false
```

## Running the Stack

Start all containers from the project root:

```powershell
docker compose up -d --build
```

Verify all 5 containers are running:

```powershell
docker ps
```

Access the interfaces:

```
Kibana:        http://localhost:5601
Elasticsearch: http://localhost:9200
Microservice:  http://localhost:5000
```

## Checkout Microservice

The Flask application simulates realistic e-commerce checkout behavior.
It randomly generates four scenarios with weighted probabilities:

| Scenario | Weight | HTTP Code |
|---|---|---|
| success | 60% | 200 |
| timeout | 15% | 408 |
| payment_failed | 15% | 402 |
| out_of_stock | 10% | 404 |

Available endpoints:

```
GET /health     → service health check
GET /products   → product catalog
GET /checkout   → simulated checkout transaction
```

Generate continuous traffic:

```powershell
cd microservice
powershell -ExecutionPolicy Bypass -File generate_traffic.ps1
```

Logs are written as structured JSON to stdout, collected automatically
by the Filebeat container via the Docker socket.

## Nginx Edge Node

The Nginx web server runs on an external Ubuntu VM.
Filebeat is installed on the VM and ships access logs to Logstash.

Deploy the Filebeat configuration to the VM:

```bash
sudo cp "server conf files/nginx/filebeat.yml" /etc/filebeat/filebeat.yml
```

Update the Logstash host IP in the config:

```yaml
output.logstash:
  hosts: ["<ELK_HOST_IP>:5044"]
```

Generate mixed HTTP 200 and 404 traffic on the VM:

```bash
# Generate 200 responses
for i in {1..20}; do curl -s http://localhost/ > /dev/null; done

# Generate 404 responses
for i in {1..20}; do curl -s http://localhost/admin > /dev/null; done
for i in {1..20}; do curl -s http://localhost/checkout > /dev/null; done
```

Restart Filebeat after configuration changes:

```bash
sudo systemctl restart filebeat
sudo systemctl status filebeat
```

## Windows Edge Node

Winlogbeat runs on a Windows machine and ships Security Event logs.

Deploy the configuration:

```
server conf files/windows/winlogbeat.yml
→ C:\Program Files\Winlogbeat\winlogbeat.yml
```

Update the Logstash host:

```yaml
output.logstash:
  hosts: ["<ELK_HOST_IP>:5044"]
```

The following Security Event IDs are collected:

| Event ID | Description |
|---|---|
| 4624 | Successful logon |
| 4625 | Failed logon (brute-force detection) |

Start Winlogbeat as Administrator:

```powershell
cd "C:\Program Files\Winlogbeat"
.\winlogbeat.exe -e -c winlogbeat.yml
```

Trigger test events by attempting a login with an incorrect password
several times, then logging in successfully.

## Logstash Pipeline

Logstash applies different processing rules per source:

**Nginx logs** → Grok pattern parses raw access log strings into
structured fields: `client_ip`, `http_method`, `request_path`,
`status_code`, `response_size`, `user_agent`

**Microservice logs** → JSON filter parses structured application
logs into the `app.*` field namespace

**Windows logs** → Mutate filter tags events with
`service_type: windows` — no parsing needed as Winlogbeat
pre-structures the fields

Output indices:

```
nginx-logs-YYYY.MM.dd
microservice-logs-YYYY.MM.dd
windows-logs-YYYY.MM.dd
```

## Kibana Setup

Create three Data Views after starting the stack:

| Data View Name | Index Pattern | Timestamp |
|---|---|---|
| Nginx Logs | `nginx-logs-*` | `@timestamp` |
| Microservice Logs | `microservice-logs-*` | `@timestamp` |
| Windows Logs | `windows-logs-*` | `@timestamp` |

Useful KQL filters for exploration:

```
service_type: "nginx"
service_type: "microservice"
service_type: "windows"
tags: "error"
app.level: "WARNING"
winlog.event_id: "4625"
```

## Verifying Data Flow

Check Elasticsearch indices and document counts:

```powershell
Invoke-RestMethod "http://localhost:9200/_cat/indices?v"
```

Check Logstash is receiving data:

```powershell
docker logs logstash --tail 50
```

Check Filebeat container is running:

```powershell
docker logs filebeat --tail 50
```

Test connectivity from external VMs to Logstash port:

```bash
# On Ubuntu VM
nc -vz <ELK_HOST_IP> 5044

# On Windows
Test-NetConnection <ELK_HOST_IP> -Port 5044
```

## Stopping the Stack

Stop containers while preserving data:

```powershell
docker compose down
```

Stop and delete all data volumes:

```powershell
docker compose down -v
```
```