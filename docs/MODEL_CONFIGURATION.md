# Model configuration (to be completed on target hardware)

The required model family is NVIDIA Nemotron running locally on the GIGABYTE AI TOP ATOM. No model endpoint, runtime, or model artifact is configured in this scaffold.

Before selecting a runtime, record:

- ATOM hardware and software/runtime versions
- Exact Nemotron model identifier, quantization, and source
- Runtime and endpoint configuration
- Context length, concurrency, memory use, and measured latency
- Structured-output and tool-calling compatibility
- Startup, health-check, and failure behavior
- Evidence that prompts and documents remain on-device
- Offline verification procedure and results

Prefer vLLM with an OpenAI-compatible API only after validating compatibility with the installed model and hardware. Consider another local runtime only after equivalent checks. Do not assume two models can be loaded together; route to a smaller and larger model only if both are actually available and the resource impact has been measured. Never configure cloud inference fallback or claim local/multi-model behavior without evidence.
