#!/bin/bash
# ── Platinum Tier: Cloud VM Setup Script ─────────────────────────────────────
# Run this once on your Oracle Free VM / AWS EC2 instance (Ubuntu 22.04+)
#
# Usage:
#   chmod +x deploy_cloud.sh
#   ./deploy_cloud.sh

set -e

echo "=== Platinum Tier: Cloud VM Setup ==="

# ── 1. System dependencies ────────────────────────────────────────────────────
echo "[1/7] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y python3 python3-pip python3-venv git curl

# ── 2. Clone vault repo ───────────────────────────────────────────────────────
echo "[2/7] Setting up Vault..."
VAULT_REPO="${GIT_REMOTE:-git@github.com:yourname/ai-employee-vault.git}"
VAULT_DIR="./Vault"

if [ ! -d "$VAULT_DIR/.git" ]; then
    git clone "$VAULT_REPO" "$VAULT_DIR"
    echo "Vault cloned from $VAULT_REPO"
else
    echo "Vault already exists, pulling latest..."
    git -C "$VAULT_DIR" pull --rebase origin main
fi

# ── 3. Python virtual environment ─────────────────────────────────────────────
echo "[3/7] Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# ── 4. Install dependencies ───────────────────────────────────────────────────
echo "[4/7] Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r PlatinumTier/requirements.txt -q

# Install Playwright browsers
playwright install chromium
playwright install-deps chromium

# ── 5. Environment file ───────────────────────────────────────────────────────
echo "[5/7] Setting up environment..."
if [ ! -f "PlatinumTier/.env" ]; then
    cp PlatinumTier/.env.example PlatinumTier/.env
    echo "⚠️  Created PlatinumTier/.env — please fill in your credentials before starting!"
else
    echo ".env already exists."
fi

# Set AGENT_MODE=cloud in .env
sed -i 's/^AGENT_MODE=.*/AGENT_MODE=cloud/' PlatinumTier/.env
sed -i 's/^AGENT_NAME=.*/AGENT_NAME=cloud/' PlatinumTier/.env

# ── 6. Create log directories ─────────────────────────────────────────────────
echo "[6/7] Creating log directories..."
mkdir -p GoldTier/logs
mkdir -p Vault/In_Progress/cloud
mkdir -p Vault/In_Progress/local
mkdir -p Vault/Plans
mkdir -p Vault/Pending_Approval
mkdir -p Vault/Approved
mkdir -p Vault/Rejected
mkdir -p Vault/Updates

# ── 7. Install systemd service ────────────────────────────────────────────────
echo "[7/7] Installing systemd service..."
WORK_DIR="$(pwd)"
VENV_PYTHON="$WORK_DIR/.venv/bin/python"

cat > /tmp/ai-employee-cloud.service << EOF
[Unit]
Description=AI Employee – Cloud Orchestrator (Platinum Tier)
After=network.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$WORK_DIR/PlatinumTier
EnvironmentFile=$WORK_DIR/PlatinumTier/.env
ExecStart=$VENV_PYTHON cloud_orchestrator.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/ai-employee-cloud.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ai-employee-cloud
echo ""
echo "=== Setup complete! ==="
echo ""
echo "Next steps:"
echo "  1. Fill in PlatinumTier/.env with your real credentials"
echo "  2. sudo systemctl start ai-employee-cloud"
echo "  3. sudo journalctl -u ai-employee-cloud -f   (to watch logs)"
echo ""
echo "Health monitor:"
echo "  source .venv/bin/activate"
echo "  python PlatinumTier/health_monitor.py"
