#!/bin/bash
# setup_file_sharing.sh - Network File Sharing Setup Script
# This script sets up SSH, Samba, and NFS servers for file sharing

set -e

echo "=== Network File Sharing Setup Script ==="
echo "Setting up SSH, Samba, and NFS servers..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script with sudo"
    exit 1
fi

# Get the current user (the one who ran sudo)
ACTUAL_USER=$(logname 2>/dev/null || echo $SUDO_USER)
USER_HOME="/home/$ACTUAL_USER"
SHARED_DIR="$USER_HOME/shared"

echo "Setting up for user: $ACTUAL_USER"
echo "User home: $USER_HOME"
echo "Shared directory: $SHARED_DIR"

# Update package list
echo "Updating package list..."
apt update

# Install required packages
echo "Installing SSH, Samba, and NFS servers..."
apt install -y openssh-server samba nfs-kernel-server

# Create shared directory
echo "Creating shared directory at $SHARED_DIR..."
mkdir -p "$SHARED_DIR"
chown $ACTUAL_USER:$ACTUAL_USER "$SHARED_DIR"
chmod 755 "$SHARED_DIR"

# Create a test file
echo "This is a test file in the shared directory" > "$SHARED_DIR/test.txt"
chown $ACTUAL_USER:$ACTUAL_USER "$SHARED_DIR/test.txt"

# Configure SSH (enable if not already enabled)
echo "Configuring SSH server..."
systemctl enable ssh
systemctl start ssh

# Configure Samba
echo "Configuring Samba..."
cp /etc/samba/smb.conf /etc/samba/smb.conf.backup

# Add shared folder configuration to Samba
cat >> /etc/samba/smb.conf << EOF

[shared]
    comment = Shared Directory
    path = $SHARED_DIR
    browseable = yes
    read only = no
    guest ok = no
    valid users = $ACTUAL_USER
    create mask = 0775
    directory mask = 0775
EOF

# Restart Samba services
systemctl enable smbd
systemctl enable nmbd
systemctl restart smbd
systemctl restart nmbd

echo "Please set a Samba password for user $ACTUAL_USER:"
smbpasswd -a $ACTUAL_USER

# Configure NFS
echo "Configuring NFS..."
cp /etc/exports /etc/exports.backup

# Add NFS export (allowing access from local network)
LOCAL_NETWORK=$(ip route | grep -E '192\.168\.|10\.|172\.' | head -1 | awk '{print $1}' | grep -E '192\.168\.|10\.|172\.')
if [ -z "$LOCAL_NETWORK" ]; then
    LOCAL_NETWORK="192.168.0.0/16"
fi

echo "$SHARED_DIR $LOCAL_NETWORK(rw,sync,no_subtree_check,no_root_squash)" >> /etc/exports

# Export NFS shares
exportfs -a
systemctl enable nfs-kernel-server
systemctl restart nfs-kernel-server

# Configure firewall (UFW)
echo "Configuring firewall..."
ufw --force enable

# Allow SSH
ufw allow ssh

# Allow Samba
ufw allow 139
ufw allow 445

# Allow NFS
ufw allow 2049
ufw allow 111

# Get IP address
IP_ADDRESS=$(hostname -I | awk '{print $1}')

echo ""
echo "=== Setup Complete! ==="
echo "Shared directory: $SHARED_DIR"
echo "Server IP address: $IP_ADDRESS"
echo ""
echo "Services configured:"
echo "- SSH: Port 22"
echo "- Samba/SMB: Ports 139, 445"
echo "- NFS: Port 2049"
echo ""
echo "To connect from another machine:"
echo "1. SSH: ssh $ACTUAL_USER@$IP_ADDRESS"
echo "2. SMB: smb://$IP_ADDRESS/shared"
echo "3. NFS: mount -t nfs $IP_ADDRESS:$SHARED_DIR /mnt/shared"
echo ""
echo "Use the connect_shared_folder.sh script on the client machine to connect easily."