#!/bin/bash
# serve_setup_script.sh - Simple HTTP server to share the setup script

echo "=== File Sharing Setup Server ==="
echo "Starting HTTP server to share setup script..."
echo ""
echo "The setup script will be available at:"
echo "  http://$(hostname -I | awk '{print $1}'):8000/setup_file_sharing.sh"
echo ""
echo "On the remote computer, download and run with:"
echo "  wget http://$(hostname -I | awk '{print $1}'):8000/setup_file_sharing.sh"
echo "  sudo bash setup_file_sharing.sh"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Python HTTP server in the current directory
python3 -m http.server 8000