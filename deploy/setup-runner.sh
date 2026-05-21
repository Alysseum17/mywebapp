#!/bin/bash

set -euo pipefail

RUNNER_USER="gha-runner"
RUNNER_DIR="/opt/actions-runner"

if [[ $EUID -ne 0 ]]; then
    echo "Run as root: sudo bash setup-runner.sh" >&2
    exit 1
fi

echo "[+] Installing prerequisites..."
apt-get update -y -q
apt-get install -y -q \
    curl \
    tar \
    jq \
    git \
    openssh-client \
    ca-certificates

echo "[+] Creating runner user '${RUNNER_USER}'..."
if ! id "$RUNNER_USER" &>/dev/null; then
    useradd -m -s /bin/bash "$RUNNER_USER"
fi

echo "[+] Preparing ${RUNNER_DIR}..."
mkdir -p "$RUNNER_DIR"
chown "${RUNNER_USER}:${RUNNER_USER}" "$RUNNER_DIR"

echo "[+] Resolving latest runner version..."
version="$(curl -fsSL https://api.github.com/repos/actions/runner/releases/latest \
    | jq -r '.tag_name' | sed 's/^v//')"
echo "    Runner version: ${version}"

tarball="actions-runner-linux-x64-${version}.tar.gz"
url="https://github.com/actions/runner/releases/download/v${version}/${tarball}"

echo "[+] Downloading ${tarball}..."
sudo -u "$RUNNER_USER" curl -fsSL -o "${RUNNER_DIR}/${tarball}" "$url"

echo "[+] Extracting..."
sudo -u "$RUNNER_USER" tar -xzf "${RUNNER_DIR}/${tarball}" -C "$RUNNER_DIR"
rm -f "${RUNNER_DIR}/${tarball}"

echo "[+] Installing runner OS dependencies..."
"${RUNNER_DIR}/bin/installdependencies.sh"

echo "[+] Runner software is successfully extracted to ${RUNNER_DIR}"

cat <<EOF

 [!] Runner software is ready in ${RUNNER_DIR}

 1. Proceed to GitHub Settings -> Actions -> Runners -> Add runner and select Linux x64."
 2. Copy the registration token shown on that page.
 3. Configure as the runner user:

     sudo -u ${RUNNER_USER} bash -c 'cd ${RUNNER_DIR} && ./config.sh --url https://github.com/<OWNER>/<REPO> --token <TOKEN> --labels self-hosted,deploy --unattended'

 4. Start the runner:

      sudo -u ${RUNNER_USER} bash -c 'cd ${RUNNER_DIR} && ./run.sh'

EOF