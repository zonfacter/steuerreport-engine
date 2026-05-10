# Qwen3.6 llama.cpp Benchmark - 2026-05-08

## Setup

Host:

- CT203 `192.168.2.203`
- GPU: AMD MI50/MI60 class, ROCm via llama.cpp
- Active endpoint after test: `http://192.168.2.203:11435/v1/chat/completions`

Installed model:

- Hugging Face source: `unsloth/Qwen3.6-35B-A3B-GGUF`
- Local file: `/opt/models/qwen3.6-35b-a3b-ud-iq4_xs.gguf`
- Active alias: `qwen3.6-35b-a3b-iq4xs`
- Context: `--ctx-size 131072`
- Cache: `--cache-type-k q4_0 --cache-type-v q4_0`
- Stable MoE setting: `--n-cpu-moe 10`

The previous `qwen3-coder-30b-a3b-q4_k_m.gguf` service file was backed up on CT203 before replacing the main `11435` endpoint.

## MoE Offload Test

The `--n-cpu-moe` flag was tested because more MoE layers on GPU should improve throughput.

| model / setting | prompt tokens | output tokens | input tok/s | output tok/s | total time | VRAM used | status |
|---|---:|---:|---:|---:|---:|---:|---|
| Qwen3-Coder-30B-A3B Q4_K_M, `n-cpu-moe 35` | 55333 | 1055 | 188.79 | 9.06 | 409.50s | ~10.3 GB | old baseline |
| Qwen3.6-35B-A3B IQ4_XS, `n-cpu-moe 35` | 55234 | 1177 | 251.98 | 18.85 | 281.63s | ~6.0 GB | stable |
| Qwen3.6-35B-A3B IQ4_XS, `n-cpu-moe 10` | 55234 | 1244 | 394.03 | 27.44 | 185.51s | ~16.2 GB | stable |

Short synthetic benchmark:

| setting | prompt tokens | output tokens | input tok/s | output tok/s | total time | VRAM used | status |
|---|---:|---:|---:|---:|---:|---:|---|
| Qwen3.6 IQ4_XS, `n-cpu-moe 35` | 34040 | 75 | 274.44 | 19.86 | 127.81s | ~6.0 GB | stable |
| Qwen3.6 IQ4_XS, `n-cpu-moe 20` | 34040 | 160 | 364.16 | 27.69 | 99.25s | ~12.0 GB | stable |
| Qwen3.6 IQ4_XS, `n-cpu-moe 10` | 34040 | 160 | 461.48 | 32.93 | 78.62s | ~15.7 GB | stable |
| Qwen3.6 IQ4_XS, `n-cpu-moe 5` | - | - | - | - | - | - | abort during ROCm warmup |

Conclusion:

`--n-cpu-moe 10` is the best tested stable setting. `--n-cpu-moe 5` is too aggressive for this CT203/MI50 setup and crashes during ROCm warmup.

## Integration Change

Steuerreport runtime was updated:

- `runtime.ai_review.llama_cpp_base_url = http://192.168.2.203:11435`
- `runtime.ai_review.llama_cpp_model = qwen3.6-35b-a3b-iq4xs`
- `runtime.ai_review.llama_cpp_timeout_seconds = 900`
- `runtime.ai_review.llama_cpp_max_tokens = 1600`

Code change:

- `src/tax_engine/ai/ollama_client.py` now sends `chat_template_kwargs: {"enable_thinking": false}` for OpenAI-compatible llama.cpp JSON classification calls.

Reason:

Qwen3.6 can emit `reasoning_content` with empty normal `content` when thinking mode is enabled. For deterministic JSON classification, thinking must be disabled.

Verification:

```bash
python3 -m py_compile src/tax_engine/ai/ollama_client.py scripts/ai_pionex_address_discovery.py
PYTHONPATH=src pytest -q tests/unit/api/test_issue_endpoints.py tests/unit/security/test_secrets.py
```

Result:

`26 passed`
