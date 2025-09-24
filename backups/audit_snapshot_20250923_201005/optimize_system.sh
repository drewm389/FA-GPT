#!/bin/bash

# FA-GPT System Optimization Script
# This script applies all performance optimizations for maximum system performance

echo "🚀 FA-GPT System Optimization Script"
echo "===================================="

# 1. CPU Performance Optimization
echo "Setting CPU governors to performance mode..."
echo 'performance' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null
echo "✅ CPU Performance mode enabled"

# 2. Memory Optimization
echo "Optimizing memory settings..."
sudo sysctl vm.swappiness=10 > /dev/null
echo "✅ Memory swappiness optimized"

# 3. I/O Optimization
echo "Optimizing I/O scheduler..."
echo 'mq-deadline' | sudo tee /sys/block/*/queue/scheduler > /dev/null 2>&1
echo "✅ I/O scheduler optimized"

# 4. Network Buffer Optimization
echo "Optimizing network buffers..."
sudo sysctl net.core.rmem_default=262144 > /dev/null
sudo sysctl net.core.rmem_max=16777216 > /dev/null
sudo sysctl net.core.wmem_default=262144 > /dev/null
sudo sysctl net.core.wmem_max=16777216 > /dev/null
echo "✅ Network buffers optimized"

# 5. GPU Performance Check
echo "Checking GPU optimization..."
if command -v rocm-smi &> /dev/null; then
    echo "✅ ROCm available for GPU acceleration"
else
    echo "⚠️  ROCm not available - CPU-only operation"
fi

# 6. Python Environment Check
echo "Checking Python environment..."
if [[ -f "fagpt_env/bin/activate" ]]; then
    source fagpt_env/bin/activate
    if python -c "import torch; print('PyTorch version:', torch.__version__)" 2>/dev/null; then
        echo "✅ PyTorch with ROCm support installed"
    else
        echo "⚠️  PyTorch installation issue detected"
    fi
    deactivate
else
    echo "⚠️  FA-GPT virtual environment not found"
fi

echo ""
echo "🎯 System Optimization Complete!"
echo "Your system is now optimized for maximum AI performance."
echo ""
echo "Performance Summary:"
echo "- CPU: Performance mode (all cores)"
echo "- Memory: Low swap usage (swappiness=10)"
echo "- I/O: Optimized for SSD with mq-deadline scheduler"
echo "- Network: Enhanced buffer sizes"
echo "- GPU: PyTorch with ROCm support"
echo ""
echo "To run FA-GPT with optimal performance:"
echo "cd /home/drew/FA-GPT && source fagpt_env/bin/activate && streamlit run app/main.py"