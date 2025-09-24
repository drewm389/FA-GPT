#!/bin/bash
echo "🎯 Starting FA-GPT with ROCm GPU Support..."
export HSA_OVERRIDE_GFX_VERSION=10.3.0
export HIP_VISIBLE_DEVICES=0
docker compose up -d
echo "✅ FA-GPT started. Access at http://localhost:8501"
echo "📊 Monitor GPU with: watch -n 1 rocm-smi"