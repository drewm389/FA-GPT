#!/bin/bash
# connect_shared_folder.sh - Client script to connect to shared folders
# Usage: bash connect_shared_folder.sh [ssh|smb|nfs|unmount]

# Configuration
REMOTE_HOST="192.168.68.126"   # IP address of the remote computer
REMOTE_USER="drew"             # Change this to the remote username
SHARED_DIR="/home/drew/shared" # Remote shared directory path
LOCAL_MOUNT_DIR="$HOME/remote_shared"  # Local mount point

# Default connection method
METHOD=${1:-smb}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required packages are installed
check_dependencies() {
    case $METHOD in
        ssh)
            if ! command -v ssh &> /dev/null; then
                print_error "SSH client not found. Install with: sudo apt install openssh-client"
                exit 1
            fi
            if ! command -v sshfs &> /dev/null; then
                print_error "SSHFS not found. Install with: sudo apt install sshfs"
                exit 1
            fi
            ;;
        smb)
            if ! command -v mount.cifs &> /dev/null; then
                print_error "CIFS utilities not found. Install with: sudo apt install cifs-utils"
                exit 1
            fi
            ;;
        nfs)
            if ! command -v mount.nfs &> /dev/null; then
                print_error "NFS utilities not found. Install with: sudo apt install nfs-common"
                exit 1
            fi
            ;;
    esac
}

# Create local mount directory
create_mount_dir() {
    if [ ! -d "$LOCAL_MOUNT_DIR" ]; then
        print_status "Creating local mount directory: $LOCAL_MOUNT_DIR"
        mkdir -p "$LOCAL_MOUNT_DIR"
    fi
}

# Check if already mounted
is_mounted() {
    mount | grep -q "$LOCAL_MOUNT_DIR"
}

# Unmount function
unmount_share() {
    print_status "Unmounting shared folder..."
    
    if is_mounted; then
        if fusermount -u "$LOCAL_MOUNT_DIR" 2>/dev/null || umount "$LOCAL_MOUNT_DIR" 2>/dev/null; then
            print_success "Successfully unmounted $LOCAL_MOUNT_DIR"
        else
            print_warning "Attempting force unmount..."
            sudo umount -f "$LOCAL_MOUNT_DIR" 2>/dev/null && print_success "Force unmounted successfully" || print_error "Failed to unmount"
        fi
    else
        print_warning "No mounted share found at $LOCAL_MOUNT_DIR"
    fi
    
    # Clean up empty directory
    if [ -d "$LOCAL_MOUNT_DIR" ] && [ -z "$(ls -A "$LOCAL_MOUNT_DIR")" ]; then
        rmdir "$LOCAL_MOUNT_DIR"
        print_status "Removed empty mount directory"
    fi
}

# SSH/SSHFS connection
connect_ssh() {
    print_status "Connecting via SSH/SSHFS..."
    
    # Test SSH connection first
    print_status "Testing SSH connection to $REMOTE_USER@$REMOTE_HOST..."
    if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "$REMOTE_USER@$REMOTE_HOST" exit 2>/dev/null; then
        print_warning "SSH key authentication failed, will prompt for password"
    fi
    
    # Mount using SSHFS
    if sshfs "$REMOTE_USER@$REMOTE_HOST:$SHARED_DIR" "$LOCAL_MOUNT_DIR" -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=3; then
        print_success "Successfully mounted via SSHFS"
        print_status "Shared folder available at: $LOCAL_MOUNT_DIR"
    else
        print_error "Failed to mount via SSHFS"
        exit 1
    fi
}

# SMB/CIFS connection
connect_smb() {
    print_status "Connecting via SMB/CIFS..."
    
    # Check if credentials file exists
    CREDS_FILE="$HOME/.samba_credentials"
    
    if [ ! -f "$CREDS_FILE" ]; then
        print_status "Creating credentials file for SMB connection..."
        echo "Creating $CREDS_FILE (will be secured with 600 permissions)"
        read -p "Enter username for $REMOTE_HOST: " smb_user
        read -s -p "Enter password: " smb_pass
        echo
        
        cat > "$CREDS_FILE" << EOF
username=$smb_user
password=$smb_pass
domain=WORKGROUP
EOF
        chmod 600 "$CREDS_FILE"
        print_success "Credentials saved to $CREDS_FILE"
    fi
    
    # Mount using CIFS
    if sudo mount -t cifs "//$REMOTE_HOST/shared" "$LOCAL_MOUNT_DIR" -o credentials="$CREDS_FILE",uid=$(id -u),gid=$(id -g),iocharset=utf8; then
        print_success "Successfully mounted via SMB/CIFS"
        print_status "Shared folder available at: $LOCAL_MOUNT_DIR"
    else
        print_error "Failed to mount via SMB/CIFS"
        print_warning "Make sure the Samba service is running on $REMOTE_HOST"
        exit 1
    fi
}

# NFS connection
connect_nfs() {
    print_status "Connecting via NFS..."
    
    # Mount using NFS
    if sudo mount -t nfs "$REMOTE_HOST:$SHARED_DIR" "$LOCAL_MOUNT_DIR" -o soft,intr,rsize=8192,wsize=8192; then
        print_success "Successfully mounted via NFS"
        print_status "Shared folder available at: $LOCAL_MOUNT_DIR"
    else
        print_error "Failed to mount via NFS"
        print_warning "Make sure the NFS service is running on $REMOTE_HOST and exports are configured"
        exit 1
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 [ssh|smb|nfs|unmount]"
    echo ""
    echo "Connection methods:"
    echo "  ssh     - Connect using SSH/SSHFS (recommended for security)"
    echo "  smb     - Connect using SMB/CIFS (default, good compatibility)"
    echo "  nfs     - Connect using NFS (good performance for Linux)"
    echo "  unmount - Unmount the currently mounted share"
    echo ""
    echo "Examples:"
    echo "  $0 ssh      # Connect via SSH"
    echo "  $0 smb      # Connect via SMB (default)"
    echo "  $0 nfs      # Connect via NFS"
    echo "  $0 unmount  # Disconnect"
    echo ""
    echo "Configuration (edit this script to change):"
    echo "  Remote host: $REMOTE_HOST"
    echo "  Remote user: $REMOTE_USER"
    echo "  Remote path: $SHARED_DIR"
    echo "  Local mount: $LOCAL_MOUNT_DIR"
}

# Main execution
case $METHOD in
    ssh)
        check_dependencies
        if is_mounted; then
            print_warning "Share already mounted. Unmounting first..."
            unmount_share
        fi
        create_mount_dir
        connect_ssh
        ;;
    smb)
        check_dependencies
        if is_mounted; then
            print_warning "Share already mounted. Unmounting first..."
            unmount_share
        fi
        create_mount_dir
        connect_smb
        ;;
    nfs)
        check_dependencies
        if is_mounted; then
            print_warning "Share already mounted. Unmounting first..."
            unmount_share
        fi
        create_mount_dir
        connect_nfs
        ;;
    unmount)
        unmount_share
        ;;
    help|-h|--help)
        show_usage
        ;;
    *)
        print_error "Invalid method: $METHOD"
        show_usage
        exit 1
        ;;
esac

# Show status after mounting
if [ "$METHOD" != "unmount" ] && [ "$METHOD" != "help" ] && [ "$METHOD" != "-h" ] && [ "$METHOD" != "--help" ]; then
    echo ""
    print_status "Connection details:"
    echo "  Method: $METHOD"
    echo "  Remote: $REMOTE_HOST"
    echo "  Local mount: $LOCAL_MOUNT_DIR"
    echo ""
    print_status "To unmount later, run: $0 unmount"
    
    # Show mounted directory contents
    if is_mounted && [ -d "$LOCAL_MOUNT_DIR" ]; then
        echo ""
        print_status "Contents of shared directory:"
        ls -la "$LOCAL_MOUNT_DIR" 2>/dev/null || print_warning "Could not list directory contents"
    fi
fi