#!/bin/bash
echo "🎯 FA-GPT System Status:"
echo "======================="
docker compose ps
echo ""
echo "🖥️ GPU Status:"
rocm-smi
echo ""
echo "🌐 Service URLs:"
echo "• Main App: http://localhost:8501"
echo "• Neo4j: http://localhost:7474"
echo "• Ollama: http://localhost:11434"