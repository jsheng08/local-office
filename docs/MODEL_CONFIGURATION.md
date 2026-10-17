# Model configuration

Verified on 2026-10-17 from the presenter's Mac via SSH (`ssh Hackathonnode`, created by NVIDIA Sync).

## Hardware and software

- Host: `EMARQUE-DGX-J` (DGX Spark platform), NVIDIA GB10, aarch64, ~121 GB unified memory (`free -g`)
- OS: Ubuntu 24.04.5 LTS; NVIDIA driver 580.178.04, CUDA 13.0
- Runtime: vLLM 0.27.1 (OpenAI-compatible API) in Docker. Ports are bound to `127.0.0.1` on the DGX only.

## Models being served (already running when checked)

| Name | Port | Model | Max ctx | GPU mem util | Intended use |
|---|---|---|---|---|---|
| `lightning` | 9000 | `nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-NVFP4` (+ DSpark speculative draft) | 131072 | 0.30 | Requirements extraction, triage, cross-document reasoning |
| `omni` | 9001 | `nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4` | 32768 | 0.28 | Receipt and image understanding (≤4 images/prompt) |
| `nano` | 9006 | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4` | 65536 | 0.20 | Simple Q&A |

All three are loaded at the same time. With them loaded, memory use was about 109/121 GB, so there is no room for a larger model such as Nemotron Super without stopping these three.

## Access from the app

The Mac forwards the ports over SSH:

```bash
ssh -N -o ServerAliveInterval=15 -L 9000:127.0.0.1:9000 -L 9001:127.0.0.1:9001 -L 9006:127.0.0.1:9006 Hackathonnode
```

Then `http://localhost:9000/v1`, `:9001/v1` and `:9006/v1` serve `/v1/models` and `/v1/chat/completions`.

## Behaviour observed

- Reasoning is on by default: output goes to `message.reasoning` and `content` may be `null`. To get a direct answer, pass `"chat_template_kwargs": {"enable_thinking": false}`.
- `response_format: {"type": "json_schema", ...}` returned schema-valid JSON for a requirements extraction with source quotes. That call took 142 completion tokens and 2.9 s end to end on `lightning`.
- A 200-token completion with reasoning on took about 2.0 s on `lightning`.

## Not yet verified

- Tool-calling round trips (the server was started with `--enable-auto-tool-choice --tool-call-parser qwen3_coder`)
- Image input on `omni`
- Behaviour under concurrent load
- Offline operation. The DGX currently has a default route through the hotspot `172.20.10.1`.
