# MIOpen GPU Compatibility Issue - Detailed Technical Analysis

## Executive Summary

FA-GPT encounters a critical `miopenStatusInternalError` when processing documents on AMD GPUs with ROCm. This error stems from MIOpen's (AMD's machine learning library) database management system attempting to write to read-only SQLite databases. **CPU fallback is not supported** as it introduces additional PyTorch model loading complications that are more complex than the original GPU issue.

## Technical Environment

- **GPU**: AMD Radeon RX 6700 XT (gfx1030 architecture)
- **ROCm Version**: 6.2.0
- **PyTorch Version**: 2.5.1+rocm6.2
- **MIOpen**: Bundled with ROCm 6.2.0
- **Operating System**: Linux (Ubuntu-based)
- **Python Environment**: Virtual environment with ROCm-compiled PyTorch

## Root Cause Analysis

### 1. The MIOpen Database System

MIOpen uses SQLite databases to cache GPU kernel compilation results and optimization parameters:

```
Database Files Created:
- gfx1030_20.HIP.3_2_0_.udb.txt     (User database)
- gfx1030_20.HIP.3_2_0_.ufdb.txt    (User find database)
```

These databases store:
- Compiled GPU kernels for specific operations
- Performance tuning parameters
- Convolution algorithm selections
- Memory layout optimizations

### 2. The Specific Error Chain

```
Error Sequence:
1. Document processing triggers neural network convolution operations
2. PyTorch calls MIOpen for GPU convolution acceleration
3. MIOpen attempts to create/update optimization databases
4. Database creation succeeds but files become read-only
5. Subsequent write attempts fail with "attempt to write a readonly database"
6. MIOpen propagates this as miopenStatusInternalError
7. PyTorch surfaces this as RuntimeError: miopenStatusInternalError
```

### 3. File Permission Investigation

**Database Location**: `~/.miopen_temp/` (configured via `MIOPEN_USER_DB_PATH`)

**Permission Analysis**:
- Directory: `drwxrwxrwx` (writable by user)
- User in correct groups: `render`, `video` (GPU access groups)
- No filesystem permission issues detected

**The Paradox**: MIOpen creates the database files successfully but then cannot write to them, suggesting an internal MIOpen state management issue rather than OS-level permissions.

### 4. Architecture-Specific Issues

The error occurs specifically with:
- **GPU Architecture**: gfx1030 (RDNA2 - Radeon RX 6700 XT)
- **ROCm Version**: 6.2.0
- **Operation Type**: 2D Convolutions in neural networks

This suggests a compatibility issue between:
1. The specific RDNA2 architecture support in MIOpen
2. The SQLite database format/locking mechanism
3. The convolution kernel compilation process

## Technical Deep Dive

### MIOpen Database Architecture

MIOpen uses a two-tier caching system:
1. **System Database**: Read-only, shared across users
2. **User Database**: Should be writable, stores user-specific optimizations

The error indicates MIOpen is treating the user database as read-only, which breaks the optimization caching mechanism.

### GPU Operation Compatibility Matrix

| Operation Type | Status | Notes |
|---------------|--------|-------|
| Basic tensor ops | ✅ Works | Simple CUDA operations |
| Matrix multiplication | ✅ Works | Uses hipBLAS (not MIOpen) |
| Convolution 2D | ❌ Fails | Requires MIOpen database |
| Neural network inference | ❌ Fails | Contains convolution layers |

### Why CPU Fallback Was Removed

CPU fallback creates additional problems:

1. **Model Loading Issues**: PyTorch models trained for CUDA cannot be easily moved to CPU
2. **Environment Variable Conflicts**: Setting `CUDA_VISIBLE_DEVICES=''` breaks model deserialization
3. **Performance Degradation**: CPU inference is 10-100x slower
4. **Memory Requirements**: CPU models have different memory layouts
5. **Dependency Complexity**: Managing dual GPU/CPU model paths is error-prone

## Attempted Solutions

### 1. Environment Variable Configuration
```bash
export MIOPEN_USER_DB_PATH=$HOME/.miopen_temp
export MIOPEN_FIND_MODE=1
export MIOPEN_DISABLE_CACHE=1
```
**Result**: Still fails - MIOpen creates files but marks them read-only

### 2. Alternative Database Locations
- System database: `/opt/rocm-6.2.0/share/miopen/db` (read-only by design)
- User database: `~/.config/miopen` (writable but same error)
- Temporary database: `/tmp/miopen-*` (writable but same error)

**Result**: Location doesn't matter - the issue is internal to MIOpen

### 3. MIOpen Debug Configuration
```bash
export MIOPEN_DEBUG_DISABLE_FIND_ENFORCE=1
export MIOPEN_FIND_MODE=1  # Fast find mode
```
**Result**: Reduces some operations but core convolution still fails

## Known Workarounds (Not Implemented)

### 1. Disable MIOpen Database Caching
- **Method**: `export MIOPEN_DISABLE_CACHE=1`
- **Trade-off**: Significant performance impact (10-50x slower)
- **Reliability**: May still fail on first kernel compilation

### 2. Use Different GPU Architecture
- **NVIDIA GPUs**: Use CUDA instead of ROCm (different ecosystem)
- **Newer AMD GPUs**: gfx1100+ may have better MIOpen support
- **Older AMD GPUs**: gfx900 series has more mature ROCm support

### 3. ROCm Version Downgrade
- **Target**: ROCm 5.4-5.7 (more stable MIOpen versions)
- **Risk**: PyTorch compatibility issues
- **Effort**: Complete environment rebuild required

## Impact on FA-GPT

### Document Processing Pipeline
```
PDF Input → Docling → Layout Detection → Convolution Operations → FAIL
                                     ↑
                                MIOpen Error
```

### Affected Components
- **Primary**: Enhanced Granite Docling document extraction
- **Secondary**: Military image analysis (Qwen VL model)
- **Tertiary**: Any CNN-based processing

### Services Still Functional
- **RAG System**: Text-based queries work if documents pre-processed
- **Ballistic Computer**: Pure mathematical calculations
- **Orders Generator**: Template-based document generation
- **Database Operations**: PostgreSQL vector storage and retrieval
- **Ollama Integration**: Text-only LLM operations

## Recommendations

### Immediate Actions
1. **Document GPU Requirements**: Clearly state NVIDIA GPU recommended
2. **Remove CPU Fallback**: Eliminate problematic fallback code (completed)
3. **Fail Fast**: Provide clear error messages about GPU compatibility

### Long-term Solutions
1. **Multi-GPU Support**: Add NVIDIA GPU compatibility
2. **Alternative Extraction**: Implement PyMuPDF fallback for basic text extraction
3. **Hybrid Architecture**: Use GPU for inference, CPU for document parsing
4. **Container Solution**: Docker with specific ROCm versions

### Development Environment
1. **NVIDIA GPU**: GTX 1080 Ti or newer for development
2. **CUDA**: Version 11.8 or 12.x with PyTorch CUDA builds
3. **ROCm Testing**: Separate environment for AMD GPU compatibility testing

## Conclusion

The MIOpen SQLite database write error is a fundamental compatibility issue between:
- AMD RDNA2 architecture (gfx1030)
- ROCm 6.2.0 MIOpen library
- SQLite database locking mechanisms

This is **not a user configuration issue** but a low-level library compatibility problem. CPU fallback introduces more complexity than it solves. The recommended approach is to require NVIDIA GPU support for production deployments while maintaining the current AMD GPU setup for testing and research.

The FA-GPT system remains highly functional for text-based operations, ballistic calculations, and military planning workflows. The GPU requirement only affects advanced document extraction capabilities that rely on computer vision models.