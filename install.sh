#!/bin/bash
##BOT MAD BY  @Hx5x5x5x @Dev_Null_X @MOTU_PATALU_HINDU_HAI

#telegram channel https://t.me/Dev_Null_X_NODE_JS

#YouTube▶️ channel https://www.youtube.com/@Dev_Null_X

#ESI CHANGE MAT KARNA BHAI PLZ RESPECT ALL DEVELOPER 

#BOT MAD BY  @Hx5x5x5x @Dev_Null_X @MOTU_PATALU_HINDU_HAI

#telegram channel https://t.me/Dev_Null_X_NODE_JS

#YouTube▶️ channel https://www.youtube.com/@Dev_Null_X

#ESI CHANGE MAT KARNA BHAI PLZ RESPECT ALL DEVELOPER 

#BOT MAD BY  @Hx5x5x5x @Dev_Null_X @MOTU_PATALU_HINDU_HAI

#telegram channel https://t.me/Dev_Null_X_NODE_JS

#YouTube▶️ channel https://www.youtube.com/@Dev_Null_X

#ESI CHANGE MAT KARNA BHAI PLZ RESPECT ALL DEVELOPER 

#BOT MAD BY  @Hx5x5x5x @Dev_Null_X @MOTU_PATALU_HINDU_HAI

#telegram channel https://t.me/Dev_Null_X_NODE_JS

#YouTube▶️ channel https://www.youtube.com/@Dev_Null_X

#ESI CHANGE MAT KARNA BHAI PLZ RESPECT ALL DEVELOPER 
###BOT MAD BY  @Hx5x5x5x @Dev_Null_X @MOTU_PATALU_HINDU_HAI

#telegram channel https://t.me/Dev_Null_X_NODE_JS

#YouTube▶️ channel https://www.youtube.com/@Dev_Null_X

#ESI CHANGE MAT KARNA BHAI PLZ RESPECT ALL DEVELOPER 

#BOT MAD BY  @Hx5x5x5x @Dev_Null_X @MOTU_PATALU_HINDU_HAI

#telegram channel https://t.me/Dev_Null_X_NODE_JS

#YouTube▶️ channel https://www.youtube.com/@Dev_Null_X

#ESI CHANGE MAT KARNA BHAI PLZ RESPECT ALL DEVELOPER 

#BOT MAD BY  @Hx5x5x5x @Dev_Null_X @MOTU_PATALU_HINDU_HAI

#telegram channel https://t.me/Dev_Null_X_NODE_JS

#YouTube▶️ channel https://www.youtube.com/@Dev_Null_X

#ESI CHANGE MAT KARNA BHAI PLZ RESPECT ALL DEVELOPER 

#BOT MAD BY  @Hx5x5x5x @Dev_Null_X @MOTU_PATALU_HINDU_HAI

#telegram channel https://t.me/Dev_Null_X_NODE_JS

#YouTube▶️ channel https://www.youtube.com/@Dev_Null_X

#ESI CHANGE MAT KARNA BHAI PLZ RESPECT ALL DEVELOPER 
#!/bin/bash
set -e

echo "🤖 VPS Bot Manager v2.0 - Installer"
echo "===================================="

# Check root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (sudo su)"
    exit 1
fi

# 1. Update system
echo "📦 Updating system..."
apt-get update -y && apt-get upgrade -y

# 2. Install essentials
echo "🔧 Installing essentials (git, curl, unzip, build-essential)..."
apt-get install -y git curl unzip build-essential python3 python3-pip python3-venv

# 3. Install Node.js 24
echo "🟢 Installing Node.js 24..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash -
    apt-get install -y nodejs
else
    echo "✅ Node.js already installed: $(node -v)"
fi

# 4. Install PM2
echo "⚙️ Installing PM2..."
npm install -g pm2
pm2 startup systemd -u root --hp /root 2>/dev/null || true

# 5. Create directories
echo "📁 Creating bot directories..."
mkdir -p /root/hosted_bots
mkdir -p /root/hosted_bots_logs

# 6. Setup Python venv
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# 7. Install Python dependencies
echo "📦 Installing Python packages..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt not found!"
fi

echo ""
echo "✅ Installation complete!"
echo "===================================="
echo "Node version: $(node -v)"
echo "NPM version:  $(npm -v)"
echo "Python:       $(python3 --version)"
echo ""
echo "📋 Next steps:"
echo "   1. cp config.py.example config.py"
echo "   2. nano config.py   ← BOT_TOKEN と ADMIN_IDS 書き換えて"
echo "   3. source venv/bin/activate"
echo "   4. python3 bot.py"
echo ""
echo "👑 Bot by @Hx5x5x5x"
echo "📢 t.me/Dev_Null_X_NODE_JS"
