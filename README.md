# mywebapp — Simple Inventory Service

Lab Work #1 — Web Service Deployment with Automation  
**Student:** IM-42, N=20

---

## Individual Assignment Variant

### Variant Calculation (N = 20)

```
V2 = (20 % 2) + 1 = 0 + 1 = 1
V3 = (20 % 3) + 1 = 2 + 1 = 3
V5 = (20 % 5) + 1 = 0 + 1 = 1
```

| Parameter | Value |
|---|---|
| V2 = 1 | Configuration via **command-line arguments** |
| V2 = 1 | Database: **MariaDB** |
| V3 = 3 | Application: **Simple Inventory** |
| V5 = 1 | Application port: **8080** |

### Application Description

**Simple Inventory** — an equipment tracking service. An inventory item contains the following fields:
- `id` — unique identifier
- `name` — item name
- `quantity` — item count
- `created_at` — record creation timestamp

---

## System Architecture

```
client → nginx (0.0.0.0:80) → mywebapp (127.0.0.1:8080) → MariaDB (127.0.0.1:3306)
```

All components are deployed on a single Linux virtual machine.  
The database and application are accessible **only locally** (127.0.0.1).  
Clients interact with the system exclusively through nginx on port 80.

---

## Repository Structure

```
mywebapp/
├── app/
│   ├── __init__.py
│   ├── database.py        # MariaDB connection pool
│   ├── main.py            # Entry point, argument parsing, uvicorn
│   └── routers/
│       ├── __init__.py
│       ├── health.py      # GET /health/alive, GET /health/ready
│       └── items.py       # GET /items, POST /items, GET /items/{id}
├── deploy/
│   ├── install.sh         # Main automation script
│   ├── mywebapp.service   # systemd service unit
│   ├── mywebapp.socket    # systemd socket unit (socket activation)
│   ├── mywebapp.nginx     # nginx configuration
│   └── sudoers-operator   # sudo rules for operator user
├── migrate.py             # Database migration script
├── pyproject.toml         # Project dependencies (uv)
└── README.md
```

---

## Web Application

### Purpose

REST API for equipment inventory management. Supports two response formats based on the `Accept` header:
- `Accept: application/json` — response in JSON format
- `Accept: text/html` — response as an HTML page with tables

### API Endpoints

#### Root Endpoint

| Method | Path | Description |
|---|---|---|
| GET | `/` | HTML page listing all business logic endpoints |

#### Business Logic

| Method | Path | Description |
|---|---|---|
| GET | `/items` | List all items (id, name) |
| POST | `/items` | Create a new item |
| GET | `/items/{id}` | Item details (id, name, quantity, created_at) |

**POST /items — request body (JSON):**
```json
{
  "name": "Laptop",
  "quantity": 5
}
```

#### Health Checks

| Method | Path | Description |
|---|---|---|
| GET | `/health/alive` | Always returns `200 OK` |
| GET | `/health/ready` | Returns `200 OK` if DB is reachable, otherwise `500` |

> **Note:** `/health/*` endpoints are blocked at the nginx level and are not accessible externally.

### Request Examples

```bash
# List items (JSON)
curl -H "Accept: application/json" http://<VM_IP>/items

# List items (HTML)
curl -H "Accept: text/html" http://<VM_IP>/items

# Create an item
curl -X POST http://<VM_IP>/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Monitor", "quantity": 3}'

# Item details
curl -H "Accept: application/json" http://<VM_IP>/items/1

# Health checks (directly from VM only)
curl http://127.0.0.1:8080/health/alive
curl http://127.0.0.1:8080/health/ready
```

---

## Development Environment

### Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — package manager
- MariaDB instance

### Installing Dependencies

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# Clone the repository
git clone https://github.com/YOUR_USERNAME/mywebapp
cd mywebapp

# Install dependencies
uv sync
```

### Running Locally

```bash
# Run the application
uv run python -m app.main \
  --host 127.0.0.1 \
  --port 8080 \
  --db-user mywebapp \
  --db-password securepass123 \
  --db-name mywebapp

# Run database migration separately
uv run python migrate.py \
  --db-user mywebapp \
  --db-password securepass123 \
  --db-name mywebapp
```

### Command-Line Arguments

| Argument | Default | Description |
|---|---|---|
| `--host` | `127.0.0.1` | Interface to listen on |
| `--port` | `8080` | Application port |
| `--db-host` | `127.0.0.1` | Database host |
| `--db-port` | `3306` | Database port |
| `--db-user` | — | Database user (required) |
| `--db-password` | — | Database password (required) |
| `--db-name` | — | Database name (required) |
| `--fd` | `None` | File descriptor for systemd socket activation |

---

## Deployment

### Base Virtual Machine Image

Official **Ubuntu 24.04.04 LTS Server** image is used:  
https://ubuntu.com/download/server#manual-install-tab
https://ubuntu.com/download/server/thank-you?version=24.04.4&architecture=amd64&lts=true

### VM Resource Requirements

| Resource | Minimum | Recommended |
|---|---|---|
| CPU | 1 core | 2 cores |
| RAM | 1 GB | 2 GB |
| Disk | 10 GB | 20 GB |
| Network | NAT | NAT or Bridge |

### OS Installation Notes

When installing Ubuntu Server:
- Select **Ubuntu Server** (not minimized)
- Enable **Install OpenSSH server** — required
- Disk partitioning: default (Use entire disk)
- Default username: `ubuntu` (will be locked after deployment)

### Connecting to the VM

**SSH:**
```bash
ssh ubuntu@<VM_IP>
```

**Default credentials (before running install.sh):**

| Field | Value |
|---|---|
| User | `ubuntu` |
| Password | set during OS installation |

**After running install.sh** the `ubuntu` user is locked. Use:

| User | Password | Permissions |
|---|---|---|
| `student` | `12345678` | sudo (password change required on first login) |
| `teacher` | `12345678` | sudo (password change required on first login) |
| `operator` | `12345678` | manage mywebapp service and nginx reload only |

To find the VM IP address via console:
```bash
ip addr show | grep 'inet '
```

### Running the Deployment Automation

```bash
# 1. Clone the repository onto the VM
git clone https://github.com/YOUR_USERNAME/mywebapp
cd mywebapp

# 2. Run the script as root
sudo bash deploy/install.sh
```

The script performs the following steps:
1. Install packages: nginx, mariadb-server, curl, git, uv
2. Create system users: student, teacher, mywebapp, operator
3. Create MariaDB database and application user
4. Copy the application to `/opt/mywebapp` and install Python dependencies
5. Install systemd service with socket activation
6. Start the service
7. Configure nginx as reverse proxy
8. Create `/home/student/gradebook` containing N=20
9. Lock the default `ubuntu` user

### System Users

| User | Purpose | Permissions |
|---|---|---|
| `student` | Development and administration | sudo |
| `teacher` | Lab work verification | sudo |
| `mywebapp` | System user that runs the app | minimal |
| `operator` | Service management | start/stop/restart/status mywebapp, reload nginx |

### systemd

The application uses **socket activation** — systemd holds the socket open on port 8080 and spawns the process only when the first request arrives.

```bash
# Status
sudo systemctl status mywebapp
sudo systemctl status mywebapp.socket

# Service management (operator or student)
sudo systemctl start mywebapp
sudo systemctl stop mywebapp
sudo systemctl restart mywebapp

# Logs
sudo journalctl -u mywebapp -f
sudo journalctl -u mywebapp -n 50
```

---

## Testing the Deployed System

### 1. Check Services

```bash
sudo systemctl status mariadb
sudo systemctl status mywebapp.socket
sudo systemctl status nginx
```

### 2. Check Network Bindings

```bash
# Application must listen on localhost only
sudo ss -tlnp | grep 8080
# Expected: 127.0.0.1:8080

# nginx must listen on all interfaces
sudo ss -tlnp | grep :80
# Expected: 0.0.0.0:80
```

### 3. Test API via nginx (port 80)

```bash
VM_IP=$(hostname -I | awk '{print $1}')

# Root endpoint
curl -H "Accept: text/html" http://$VM_IP/

# List items (JSON)
curl -H "Accept: application/json" http://$VM_IP/items

# Create an item
curl -X POST http://$VM_IP/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Laptop", "quantity": 5}'

# Item details
curl -H "Accept: application/json" http://$VM_IP/items/1

# Health endpoint must be blocked by nginx — expect 404
curl -v http://$VM_IP/health/alive
```

### 4. Test Health Directly (from VM only)

```bash
curl http://127.0.0.1:8080/health/alive
# OK

curl http://127.0.0.1:8080/health/ready
# OK
```

### 5. Verify Database Is Not Accessible Externally

```bash
# From the host machine — connection must be refused
mysql -h <VM_IP> -u mywebapp -p mywebapp
# ERROR 2003 (HY000): Can't connect to MySQL server
```

### 6. Test operator User Restrictions

```bash
su - operator
# password: 12345678

sudo systemctl status mywebapp    # OK
sudo systemctl restart mywebapp   # OK
sudo systemctl reload nginx       # OK
sudo systemctl status mariadb     # DENIED — sudo error
```

### 7. Verify Gradebook

```bash
cat /home/student/gradebook
# 20
```
