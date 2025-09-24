#!/bin/bash
echo "🎯 Starting FA-GPT with ROCm GPU Support..."

# Configure MIOpen environment for stable GPU acceleration (fixes backend mixing issues)
echo "🔧 Configuring MIOpen environment..."
export MIOPEN_ENABLE_SQLITE_KERNDB=0
export MIOPEN_ENABLE_SQLITE_PERFDB=0
export MIOPEN_USER_DB_PATH=/home/drew/miopen_cache/textdb
export MIOPEN_DISABLE_PERFDB=0
export MIOPEN_FIND_ENFORCE=SEARCH
export MIOPEN_USE_GEMM=1
export MIOPEN_DEBUG_DISABLE_MLIR=1

# ROCm GPU configuration
export HSA_OVERRIDE_GFX_VERSION=10.3.0
export PYTORCH_ROCM_ARCH=gfx1030
export HIP_VISIBLE_DEVICES=0

# Ensure MIOpen cache directory exists and is writable
mkdir -p /home/drew/miopen_cache/textdb
chmod -R 775 /home/drew/miopen_cache
echo "✅ MIOpen cache configured at: /home/drew/miopen_cache"
docker compose up -d
echo "✅ FA-GPT started. Access at http://localhost:8501"
echo "📊 Monitor GPU with: watch -n 1 rocm-smi"