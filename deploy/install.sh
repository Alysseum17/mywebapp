#!/bin/bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
die()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }

[[ $EUID -ne 0 ]] && die "Run as root: sudo bash install.sh"

N=20
APP_DIR="/opt/mywebapp"
DB_NAME="mywebapp"
DB_USER="mywebapp"
DB_PASS="securepass123"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DEFAULT_PASSWORD="12345678"

log "Starting deployment of mywebapp (N=${N})"

log "Step 1: Installing packages..."

apt-get update -y -q
apt-get install -y -q \
    curl \
    git \
    nginx \
    mariadb-server

log "Packages installed"

if ! command -v uv &>/dev/null; then
    log "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | env HOME=/root sh
    cp /root/.local/bin/uv /usr/local/bin/uv
fi

log "uv: $(uv --version)"

log "Step 2: Creating users..."

create_user() {
    local username=$1
    local is_system=${2:-false}

    if id "$username" &>/dev/null; then
        warn "User $username already exists, skipping"
        return
    fi

    local group_arg=""
    if getent group "$username" &>/dev/null; then
        group_arg="-g $username"
    fi

    if [[ "$is_system" == "true" ]]; then
        useradd -r -s /usr/sbin/nologin -d "$APP_DIR" $group_arg "$username"
        log "System user $username created"
    else
        useradd -m -s /bin/bash $group_arg "$username"
        echo "${username}:${DEFAULT_PASSWORD}" | chpasswd
        chage -d 0 "$username"
        log "User $username created (password: ${DEFAULT_PASSWORD}, change on login)"
    fi
}

create_user student
usermod -aG sudo student

create_user teacher
usermod -aG sudo teacher

create_user mywebapp true

create_user operator

cp "$SCRIPT_DIR/sudoers-operator" /etc/sudoers.d/operator
chmod 440 /etc/sudoers.d/operator

visudo -c -f /etc/sudoers.d/operator || die "Error in sudoers file"
log "sudo rights for operator configured"

log "Step 3: Configuring MariaDB..."

systemctl enable --now mariadb

for i in {1..10}; do
    mysqladmin ping &>/dev/null && break
    warn "Waiting for MariaDB... (${i}/10)"
    sleep 2
done

mysqladmin ping &>/dev/null || die "MariaDB failed to start"

mysql -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME} \
    CHARACTER SET utf8mb4 \
    COLLATE utf8mb4_unicode_ci;"

mysql -e "CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' \
    IDENTIFIED BY '${DB_PASS}';"

mysql -e "GRANT ALL PRIVILEGES ON ${DB_NAME}.* \
    TO '${DB_USER}'@'localhost';"

mysql -e "FLUSH PRIVILEGES;"

log "DB ${DB_NAME} and user ${DB_USER} created"

log "Step 4: Copying application..."

rm -rf "$APP_DIR"
cp -r "$PROJECT_DIR" "$APP_DIR"
chown -R mywebapp:mywebapp "$APP_DIR"

log "Installing Python dependencies..."
cd "$APP_DIR"
sudo -u mywebapp /usr/local/bin/uv sync

mkdir -p /etc/mywebapp
cat > /etc/mywebapp/env << EOF
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASS}
DB_NAME=${DB_NAME}
DB_HOST=127.0.0.1
DB_PORT=3306
EOF

chown root:mywebapp /etc/mywebapp/env
chmod 640 /etc/mywebapp/env
log "Config /etc/mywebapp/env created"

log "Step 5: Configuring systemd..."

cp "$SCRIPT_DIR/mywebapp.service" /etc/systemd/system/mywebapp.service
cp "$SCRIPT_DIR/mywebapp.socket"  /etc/systemd/system/mywebapp.socket

systemctl daemon-reload
systemctl enable mywebapp.socket
log "systemd unit files installed"

log "Step 6: Starting service..."

systemctl start mywebapp.socket

sleep 2
systemctl is-active mywebapp.socket || die "mywebapp.socket failed to start"

curl -s http://127.0.0.1:8080/health/ready || warn "Service is still starting..."
sleep 3

curl -s http://127.0.0.1:8080/health/ready | grep -q "OK" \
    || die "Application not responding to /health/ready"

log "Application started and responding"

log "Step 7: Configuring nginx..."

cp "$SCRIPT_DIR/mywebapp.nginx" /etc/nginx/sites-available/mywebapp

ln -sf /etc/nginx/sites-available/mywebapp \
       /etc/nginx/sites-enabled/mywebapp

rm -f /etc/nginx/sites-enabled/default

nginx -t || die "Error in nginx configuration"

systemctl enable --now nginx
systemctl reload nginx

log "nginx configured"

log "Step 8: Gradebook..."

echo "$N" > /home/student/gradebook
chown student:student /home/student/gradebook
chmod 644 /home/student/gradebook
log "File /home/student/gradebook created (N=${N})"

DEFAULT_USER=$(getent passwd 1000 | cut -d: -f1 || echo "")

if [[ -n "$DEFAULT_USER" ]] && \
   [[ "$DEFAULT_USER" != "student" ]] && \
   [[ "$DEFAULT_USER" != "teacher" ]]; then
    usermod -L "$DEFAULT_USER"
    warn "Default user '${DEFAULT_USER}' blocked"
fi

echo ""
log "  Final system check"

check() {
    local desc=$1
    local cmd=$2
    if eval "$cmd" &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $desc"
    else
        echo -e "  ${RED}✗${NC} $desc"
    fi
}

check "MariaDB is running"          "systemctl is-active mariadb"
check "mywebapp.socket is active"   "systemctl is-active mywebapp.socket"
check "nginx is running"            "systemctl is-active nginx"
check "GET /health/alive → OK"      "curl -sf http://127.0.0.1:8080/health/alive | grep -q OK"
check "GET / via nginx"             "curl -sf -H 'Accept: text/html' http://127.0.0.1/ | grep -q '/items'"
check "GET /items via nginx"        "curl -sf http://127.0.0.1/items"
check "health blocked by nginx"     "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1/health/alive | grep -q 404"
check "gradebook exists"            "test -f /home/student/gradebook"

echo ""
log "Deployment completed!"
log "Machine IP: $(hostname -I | awk '{print $1}')"
log "Open in browser: http://$(hostname -I | awk '{print $1}')/"
