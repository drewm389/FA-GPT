#!/bin/bash

# FA-GPT Performance Monitor
# Monitors system performance metrics for optimal AI operation

echo "🔍 FA-GPT Performance Monitor"
echo "============================="

# System Overview
echo "📊 System Overview:"
echo "Hostname: $(hostname)"
echo "Uptime: $(uptime -p)"
echo "Load Average: $(uptime | awk -F'load average:' '{print $2}')"
echo ""

# CPU Information
echo "🖥️  CPU Performance:"
echo "CPU Model: $(lscpu | grep 'Model name' | awk -F: '{print $2}' | xargs)"
echo "CPU Cores: $(nproc)"
echo "CPU Frequency:"
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq; do
    if [[ -r "$cpu" ]]; then
        freq=$(cat "$cpu")
        cpu_num=$(echo "$cpu" | grep -o 'cpu[0-9]*' | grep -o '[0-9]*')
        echo "  CPU${cpu_num}: $((freq/1000)) MHz"
    fi
done | head -6

echo "CPU Governors:"
governors=($(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort | uniq -c))
echo "  ${governors[1]} cores in ${governors[0]} mode"

echo ""

# Memory Information
echo "💾 Memory Performance:"
free_output=$(free -h)
echo "Memory Usage:"
echo "$free_output" | grep -E "(Mem:|Swap:)"
echo "Swappiness: $(cat /proc/sys/vm/swappiness)"
echo ""

# GPU Information
echo "🎮 GPU Performance:"
if command -v rocm-smi &> /dev/null; then
    echo "ROCm GPU Status:"
    rocm-smi --showtemp --showpower --showuse 2>/dev/null || echo "  ROCm tools available but GPU not detected"
elif lspci | grep -i amd | grep -i vga &> /dev/null; then
    echo "AMD GPU detected:"
    lspci | grep -i amd | grep -i vga
else
    echo "No compatible GPU detected"
fi
echo ""

# Storage Performance
echo "💿 Storage Performance:"
echo "Disk Usage:"
df -h / | tail -1
echo "I/O Scheduler:"
for device in /sys/block/sd*/queue/scheduler; do
    if [[ -r "$device" ]]; then
        disk=$(echo "$device" | cut -d'/' -f4)
        scheduler=$(cat "$device" | grep -o '\[.*\]' | tr -d '[]')
        echo "  $disk: $scheduler"
    fi
done
echo ""

# Network Performance
echo "🌐 Network Performance:"
echo "Network Buffer Sizes:"
echo "  rmem_default: $(cat /proc/sys/net/core/rmem_default)"
echo "  rmem_max: $(cat /proc/sys/net/core/rmem_max)"
echo "  wmem_default: $(cat /proc/sys/net/core/wmem_default)"  
echo "  wmem_max: $(cat /proc/sys/net/core/wmem_max)"
echo ""

# AI Environment Status
echo "🤖 AI Environment Status:"
if [[ -f "fagpt_env/bin/activate" ]]; then
    source fagpt_env/bin/activate
    echo "Virtual Environment: ✅ Active"
    
    if python -c "import torch" 2>/dev/null; then
        pytorch_version=$(python -c "import torch; print(torch.__version__)" 2>/dev/null)
        echo "PyTorch: ✅ v$pytorch_version"
        
        rocm_available=$(python -c "import torch; print('Yes' if hasattr(torch.version, 'hip') and torch.version.hip is not None else 'No')" 2>/dev/null)
        echo "ROCm Support: $([[ $rocm_available == "Yes" ]] && echo "✅" || echo "❌") $rocm_available"
    else
        echo "PyTorch: ❌ Not installed"
    fi
    
    if python -c "import streamlit" 2>/dev/null; then
        echo "Streamlit: ✅ Available"
    else
        echo "Streamlit: ❌ Not installed" 
    fi
    
    if python -c "import ollama" 2>/dev/null; then
        echo "Ollama: ✅ Available"
    else
        echo "Ollama: ❌ Not installed"
    fi
    
    deactivate
else
    echo "Virtual Environment: ❌ Not found"
fi
echo ""

# Performance Score
echo "🏆 Performance Score:"
score=0

# CPU Score (25 points)
performance_cores=$(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | grep -c "performance")
total_cores=$(nproc)
cpu_score=$((performance_cores * 25 / total_cores))
score=$((score + cpu_score))

# Memory Score (25 points)  
swappiness=$(cat /proc/sys/vm/swappiness)
mem_score=$((25 - swappiness / 4))
score=$((score + mem_score))

# GPU Score (25 points)
if python -c "import torch; exit(0 if hasattr(torch.version, 'hip') and torch.version.hip is not None else 1)" 2>/dev/null; then
    gpu_score=25
else
    gpu_score=0
fi
score=$((score + gpu_score))

# Environment Score (25 points)
env_score=0
if [[ -f "fagpt_env/bin/activate" ]]; then
    env_score=$((env_score + 5))
    source fagpt_env/bin/activate
    python -c "import torch" 2>/dev/null && env_score=$((env_score + 10))
    python -c "import streamlit" 2>/dev/null && env_score=$((env_score + 5))
    python -c "import ollama" 2>/dev/null && env_score=$((env_score + 5))
    deactivate
fi
score=$((score + env_score))

echo "Overall Performance: $score/100"
if [[ $score -ge 90 ]]; then
    echo "Status: 🚀 Excellent - System fully optimized!"
elif [[ $score -ge 75 ]]; then
    echo "Status: ✅ Good - Minor optimizations possible"
elif [[ $score -ge 50 ]]; then
    echo "Status: ⚠️  Fair - Several optimizations needed"
else
    echo "Status: ❌ Poor - Major optimizations required"
fi

echo ""
echo "💡 Recommendations:"
[[ $cpu_score -lt 25 ]] && echo "  - Run: sudo cpufreq-set -g performance (for all cores)"
[[ $mem_score -lt 20 ]] && echo "  - Run: sudo sysctl vm.swappiness=10"
[[ $gpu_score -lt 25 ]] && echo "  - Install PyTorch with ROCm support"
[[ $env_score -lt 20 ]] && echo "  - Install missing Python packages"