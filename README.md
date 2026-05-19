# ELK Hub

ELK Hub is a lab project for collecting and analyzing logs from three sources:

- A Dockerized `checkout-microservice`
- An Nginx server running on a separate Ubuntu VM
- A Windows Server VM sending Windows Security events

Logs are shipped to Logstash, parsed/enriched, stored in Elasticsearch, and explored in Kibana.

## Architecture

```text
Checkout microservice container
  -> Filebeat container
  -> Logstash :5044
  -> Elasticsearch
  -> Kibana

Ubuntu Nginx VM
  -> Filebeat on VM
  -> Logstash :5044 on ELK host
  -> Elasticsearch
  -> Kibana

Windows Server VM
  -> Winlogbeat on VM
  -> Logstash :5044 on ELK host
  -> Elasticsearch
  -> Kibana
```

## Project Structure

```text
.
+-- docker-compose.yml
+-- .env
+-- logstash.conf
+-- microservice/
|   +-- app.py
|   +-- DockerFile
|   +-- filebeat.yml
|   +-- generate_traffic.ps1
|   +-- requirements.txt
+-- server conf files/
    +-- nginx/
    |   +-- filebeat.yml
    |   +-- sample_nginx.log
    +-- windows server/
        +-- winlogbeat.yml
        +-- sample_windows_events.txt
```

## Services

The Docker Compose stack starts:

- `elasticsearch` on port `9200`
- `kibana` on port `5601`
- `logstash` listening for Beats on port `5044`
- `checkout-microservice` on port `5000`
- `filebeat`, which reads Docker container logs from the checkout microservice

The Nginx and Windows Server machines are external VMs. They are not started by Docker Compose.

## Requirements

- Docker Desktop or Docker Engine
- Docker Compose
- PowerShell, for the traffic generator
- Ubuntu VM with Nginx and Filebeat installed
- Windows Server VM with Winlogbeat installed
- Network connectivity from both VMs to the ELK host on port `5044`

## Environment

Main settings are stored in `.env`:

```env
STACK_VERSION=8.7.1
CLUSTER_NAME=ELK-cluster
ES_PORT=9200
KIBANA_PORT=5601
ES_MEM_LIMIT=1g
```

Security is disabled for Elasticsearch in `docker-compose.yml`:

```yaml
xpack.security.enabled=false
```

This setup is intended for a local lab environment, not production.

## Start the ELK Stack

From the project root:

```powershell
docker compose up -d --build
```

Check container status:

```powershell
docker compose ps
```

Open Kibana:

```text
http://localhost:5601
```

Check Elasticsearch:

```text
http://localhost:9200
```

## Checkout Microservice

The checkout service exposes:

- `GET /health`
- `GET /products`
- `GET /checkout`

Test it from the host:

```powershell
Invoke-WebRequest http://localhost:5000/health
Invoke-WebRequest http://localhost:5000/products
Invoke-WebRequest http://localhost:5000/checkout
```

Generate continuous sample traffic:

```powershell
.\microservice\generate_traffic.ps1
```

The service writes JSON logs to stdout. The Docker Filebeat container reads those logs and sends only the `checkout-microservice` container logs to Logstash.

## Nginx VM Setup

Nginx runs on a separate Ubuntu VM.

Copy this config to the VM Filebeat config path:

```text
server conf files/nginx/filebeat.yml
```

Typical destination on Ubuntu:

```bash
/etc/filebeat/filebeat.yml
```

Important setting:

```yaml
output.logstash:
  hosts: ["192.168.230.1:5044"]
```

Replace `192.168.230.1` with the IP address of the machine running Docker Compose if it changes.

Restart Filebeat on the Ubuntu VM:

```bash
sudo filebeat test config
sudo filebeat test output
sudo systemctl restart filebeat
sudo systemctl status filebeat
```

The Nginx Filebeat config reads:

```text
/var/log/nginx/access.log
```

Generate Nginx traffic by visiting the Nginx VM in a browser or with curl:

```bash
curl http://localhost
```

## Windows Server VM Setup

Windows Server runs on a separate VM.

Copy this config to the Winlogbeat install directory:

```text
server conf files/windows server/winlogbeat.yml
```

Typical destination:

```text
C:\Program Files\Winlogbeat\winlogbeat.yml
```

Important setting:

```yaml
output.logstash:
  hosts: ["192.168.230.1:5044"]
```

Replace `192.168.230.1` with the IP address of the machine running Docker Compose if it changes.

This config collects Windows Security events:

- `4624`: successful logon
- `4625`: failed logon

Run these commands in PowerShell as Administrator on the Windows Server VM:

```powershell
cd "C:\Program Files\Winlogbeat"
.\winlogbeat.exe test config
.\winlogbeat.exe test output
Start-Service winlogbeat
Get-Service winlogbeat
```

Generate sample Windows events by logging in successfully or attempting a login with an incorrect password.

## Logstash Routing

Logstash listens on port `5044` for Beats input.

It writes logs to these Elasticsearch indices:

```text
nginx-logs-YYYY.MM.dd
microservice-logs-YYYY.MM.dd
windows-logs-YYYY.MM.dd
```

Routing rules are defined in:

```text
logstash.conf
```

Nginx logs are parsed with a Grok pattern, microservice logs are parsed as JSON, and Windows logs are tagged as `service_type: windows`.

## Kibana

In Kibana, create data views for:

```text
nginx-logs-*
microservice-logs-*
windows-logs-*
```

Use `@timestamp` as the time field.

Useful filters:

```text
service_type: nginx
service_type: microservice
service_type: windows
tags: error
tags: success
```

## Troubleshooting

Check Logstash logs:

```powershell
docker logs logstash
```

Check Filebeat container logs:

```powershell
docker logs filebeat
```

Check Elasticsearch indices:

```powershell
Invoke-RestMethod http://localhost:9200/_cat/indices?v
```

Check that Logstash port `5044` is reachable from each VM:

```powershell
Test-NetConnection 192.168.230.1 -Port 5044
```

On Ubuntu:

```bash
nc -vz 192.168.230.1 5044
```

If VM logs are not arriving:

- Confirm the VM can reach the ELK host IP.
- Confirm port `5044` is open in the host firewall.
- Confirm Filebeat or Winlogbeat is running on the VM.
- Confirm the `hosts` value points to the Docker Compose host, not to the VM itself.

## Stop the Stack

```powershell
docker compose down
```

To remove volumes and delete Elasticsearch/Kibana/Logstash data:

```powershell
docker compose down -v
```
