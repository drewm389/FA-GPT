#!/usr/bin/env python3
"""
FA-GPT ROCm GPU Acceleration Test Script
Tests PyTorch GPU detection and performance with AMD RX 6700 XT
"""

import torch
import time
import sys
import os

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def test_rocm_environment():
    """Test ROCm environment variables"""
    print_section("ROCm Environment Check")
    
    env_vars = [
        'HSA_OVERRIDE_GFX_VERSION',
        'HIP_VISIBLE_DEVICES', 
        'ROCM_PATH'
    ]
    
    for var in env_vars:
        value = os.environ.get(var, "Not set")
        print(f"{var}: {value}")
    
    return all(os.environ.get(var) for var in env_vars)

def test_pytorch_rocm():
    """Test PyTorch ROCm detection and capabilities"""
    print_section("PyTorch ROCm Detection")
    
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    print(f"ROCm available: {torch.cuda.is_available()}")  # ROCm uses CUDA API
    
    if torch.cuda.is_available():
        device_count = torch.cuda.device_count()
        print(f"GPU devices detected: {device_count}")
        
        for i in range(device_count):
            device_name = torch.cuda.get_device_name(i)
            device_props = torch.cuda.get_device_properties(i)
            print(f"  Device {i}: {device_name}")
            print(f"    Total memory: {device_props.total_memory / 1024**3:.2f} GB")
            print(f"    Compute capability: {device_props.major}.{device_props.minor}")
        
        current_device = torch.cuda.current_device()
        print(f"Current device: {current_device}")
        return True
    else:
        print("❌ No GPU devices detected")
        return False

def test_basic_gpu_operations():
    """Test basic GPU tensor operations"""
    print_section("Basic GPU Operations Test")
    
    if not torch.cuda.is_available():
        print("❌ GPU not available, skipping GPU tests")
        return False
    
    try:
        # Create tensors on GPU
        device = torch.device('cuda')
        print(f"Using device: {device}")
        
        # Test tensor creation
        a = torch.randn(1000, 1000, device=device)
        b = torch.randn(1000, 1000, device=device)
        print(f"✅ Created tensors on GPU: {a.shape}")
        
        # Test basic operations
        c = torch.matmul(a, b)
        print(f"✅ Matrix multiplication successful: {c.shape}")
        
        # Test memory operations
        memory_allocated = torch.cuda.memory_allocated() / 1024**2
        memory_reserved = torch.cuda.memory_reserved() / 1024**2
        print(f"GPU memory allocated: {memory_allocated:.2f} MB")
        print(f"GPU memory reserved: {memory_reserved:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ GPU operation failed: {e}")
        return False

def benchmark_gpu_performance():
    """Benchmark GPU vs CPU performance"""
    print_section("GPU Performance Benchmark")
    
    if not torch.cuda.is_available():
        print("❌ GPU not available, running CPU-only benchmark")
        device = torch.device('cpu')
    else:
        device = torch.device('cuda')
    
    # Test matrix sizes
    sizes = [500, 1000, 2000]
    
    for size in sizes:
        print(f"\nTesting {size}x{size} matrix multiplication:")
        
        # GPU test
        if torch.cuda.is_available():
            torch.cuda.synchronize()  # Ensure GPU is ready
            
            a_gpu = torch.randn(size, size, device='cuda')
            b_gpu = torch.randn(size, size, device='cuda')
            
            start_time = time.time()
            torch.cuda.synchronize()  # Start timing
            
            c_gpu = torch.matmul(a_gpu, b_gpu)
            torch.cuda.synchronize()  # Wait for completion
            
            gpu_time = time.time() - start_time
            print(f"  GPU time: {gpu_time:.4f} seconds")
        
        # CPU test
        a_cpu = torch.randn(size, size, device='cpu')
        b_cpu = torch.randn(size, size, device='cpu')
        
        start_time = time.time()
        c_cpu = torch.matmul(a_cpu, b_cpu)
        cpu_time = time.time() - start_time
        
        print(f"  CPU time: {cpu_time:.4f} seconds")
        
        if torch.cuda.is_available():
            speedup = cpu_time / gpu_time
            print(f"  GPU speedup: {speedup:.2f}x")

def test_model_inference():
    """Test a simple neural network on GPU"""
    print_section("Neural Network GPU Test")
    
    if not torch.cuda.is_available():
        print("❌ GPU not available, skipping model test")
        return False
    
    try:
        device = torch.device('cuda')
        
        # Create a simple model
        model = torch.nn.Sequential(
            torch.nn.Linear(1000, 500),
            torch.nn.ReLU(),
            torch.nn.Linear(500, 250),
            torch.nn.ReLU(),
            torch.nn.Linear(250, 10)
        ).to(device)
        
        print(f"✅ Model created and moved to GPU")
        
        # Test inference
        batch_size = 64
        input_data = torch.randn(batch_size, 1000, device=device)
        
        with torch.no_grad():
            output = model(input_data)
        
        print(f"✅ Inference successful: input {input_data.shape} -> output {output.shape}")
        
        # Benchmark inference speed
        num_runs = 100
        start_time = time.time()
        
        with torch.no_grad():
            for _ in range(num_runs):
                _ = model(input_data)
        
        torch.cuda.synchronize()
        total_time = time.time() - start_time
        avg_time = total_time / num_runs
        
        print(f"Average inference time: {avg_time*1000:.2f} ms")
        print(f"Throughput: {batch_size/avg_time:.0f} samples/second")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

def main():
    """Run all GPU tests"""
    print("FA-GPT ROCm GPU Acceleration Test")
    print("Testing AMD RX 6700 XT with PyTorch + ROCm")
    
    results = {
        'environment': test_rocm_environment(),
        'pytorch_detection': test_pytorch_rocm(),
        'basic_operations': test_basic_gpu_operations(),
        'model_inference': test_model_inference()
    }
    
    # Run benchmark regardless of GPU availability
    benchmark_gpu_performance()
    
    # Summary
    print_section("Test Summary")
    
    passed = sum(results.values())
    total = len(results)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! GPU acceleration is working correctly.")
    elif passed >= 2:
        print("⚠️  Partial success. Check failed tests above.")
    else:
        print("❌ GPU acceleration not working. Check ROCm installation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)