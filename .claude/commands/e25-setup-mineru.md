---
description: "E25 Research Spike — OPTIONAL MinerU setup. Only run if Demi decides to include MinerU in the comparison. Run AFTER /e25-setup-docling."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# E25 Setup: MinerU (OPTIONAL)

You are Mary (BA) setting up MinerU for the E25 research spike.

## IMPORTANT: THIS IS OPTIONAL

MinerU code was deleted in E24-S3 (commit `6e0e2e8`, 2,298 lines removed). Setting up MinerU for this spike means:
1. Installing paddlepaddle-gpu (~1-2GB download)
2. Upgrading magic-pdf to >=1.3.0
3. Writing NEW spike-only extraction code (old MineruTableExtractor is gone)
4. Risk of torch/paddle CUDA conflicts

**Ask the user to confirm before proceeding.**

## MANDATORY PRE-READ

1. `docs/research/e25-environment-audit.md` — Check CUDA version from nvidia-smi output
2. `docs/sprint-artifacts/e24-s3-remove-mineru-dead-code.md` — What was removed and why

## STEP 1: Determine CUDA Version

```bash
nvidia-smi | head -3
# Look for "CUDA Version: 12.x"
```

## STEP 2: Check if magic-pdf is still installed

```bash
python -c "import magic_pdf; print(f'magic-pdf={magic_pdf.__version__}')" 2>&1
uv pip show magic-pdf 2>/dev/null || pip show magic-pdf 2>/dev/null
```

## STEP 3: Install PaddlePaddle GPU

**CRITICAL**: PaddlePaddle GPU is NOT on standard PyPI. Must use Paddle's custom index.

```bash
# For CUDA 12.x (covers 12.4-12.6):
pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/

# Alternative with uv:
uv pip install paddlepaddle-gpu==3.2.0 --index-url https://www.paddlepaddle.org.cn/packages/stable/cu126/ --break-system-packages

# For CUDA 11.8 (older systems):
# pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
```

**Verify paddle:**

```bash
python -c "
import paddle
print(f'PaddlePaddle version: {paddle.__version__}')
paddle.utils.run_check()
print(f'CUDA available: {paddle.device.is_compiled_with_cuda()}')
print(f'GPU count: {paddle.device.cuda.device_count()}')
"
```

## STEP 4: Upgrade magic-pdf

```bash
# magic-pdf 1.3.x removed detectron2 dependency and supports torch 2.2-2.6
uv pip install "magic-pdf[full]>=1.3.0" --break-system-packages
# Or: pip install "magic-pdf[full]>=1.3.0"
```

**Verify MinerU:**

```bash
python -c "
import magic_pdf
print(f'MinerU/magic-pdf version: {magic_pdf.__version__}')
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
print('✅ MinerU imports successful')
"
```

## STEP 5: Torch/Paddle Conflict Check

**THIS IS THE RISK STEP.** Both torch and paddle link CUDA libraries. They may conflict.

```bash
python -c "
# Test torch still works
import torch
t = torch.randn(3, 3).cuda()
print(f'torch GPU: OK ({t.sum().item():.4f})')

# Test paddle works
import paddle
p = paddle.randn([3, 3])
print(f'paddle: OK ({p.sum().item():.4f})')

# Test paddle GPU (if available)
try:
    if paddle.device.is_compiled_with_cuda():
        p_gpu = paddle.randn([3, 3])  # paddle may not support .cuda() directly
        print(f'paddle GPU: OK')
except Exception as e:
    print(f'paddle GPU: FAILED ({e})')

print('✅ Both torch and paddle coexist')
"
```

### If they CONFLICT:

**Option A: CPU-only paddle (MinerU still uses torch GPU for some ops)**

```bash
pip uninstall paddlepaddle-gpu -y
pip install paddlepaddle==3.2.0
```

**Option B: Separate venv for MinerU testing**

```bash
# Windows PowerShell:
python -m venv .venv-mineru
.venv-mineru\Scripts\activate
pip install "magic-pdf[full]>=1.3.0"
pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/
pip install PyMuPDF pandas tabulate

# WSL:
python -m venv .venv-mineru
source .venv-mineru/bin/activate
pip install "magic-pdf[full]>=1.3.0"
pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/
pip install PyMuPDF pandas tabulate
```

**Option C: Skip MinerU entirely**

Document the conflict and focus on Approach A (PyMuPDF + Docling Direct API).

## STEP 6: MinerU Model Weights (if paddle works)

MinerU needs its own model weights. They download automatically on first use.

```bash
# Check if magic-pdf has a model download command:
magic-pdf --help 2>/dev/null || python -m magic_pdf --help 2>/dev/null
```

## STEP 7: Update Audit Report

Update `docs/research/e25-environment-audit.md` with MinerU section:
- PaddlePaddle: ✅/❌ (version, GPU support)
- magic-pdf: ✅/❌ (version)
- Torch/Paddle coexistence: ✅/❌/CONFLICT (resolution taken)
- MinerU model weights: ✅/❌

## DO NOT

- Do NOT modify production code
- Do NOT restore deleted MinerU code to the codebase
- Do NOT add paddle to pyproject.toml (spike-only install)
- Do NOT trigger extraction pipelines
