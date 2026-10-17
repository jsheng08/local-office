#!/usr/bin/env bash
# Run ON the DGX. Downloads Nemotron 3.5 Super VL (NVFP4, ~75 GB) into the same
# Hugging Face cache the vLLM containers use, using the Python in the vLLM image.
set -euo pipefail
docker rm -f superdl >/dev/null 2>&1 || true
docker run -d --name superdl \
  -v "$HOME/.cache/huggingface:/root/.cache/huggingface" \
  --entrypoint python3 vllm/vllm-openai:v0.27.1 \
  -c "from huggingface_hub import snapshot_download; p=snapshot_download('nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-NVFP4', max_workers=16); print('DONE', p)"
echo "Started. Progress: du -sh ~/.cache/huggingface/hub/models--nvidia--NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-NVFP4"
echo "Finished when: docker logs superdl | grep DONE"
