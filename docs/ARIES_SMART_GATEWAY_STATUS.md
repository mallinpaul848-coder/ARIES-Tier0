# ARIES Smart Gateway Prototype — Scope and Validation

This commit adds a portable C++ arithmetic demonstration and a FastAPI prototype.

## Files
- `include/aries_gateway.hpp`: 16-lane illustrative field arithmetic; uses AVX-512 when explicitly compiled with `ARIES_ENABLE_AVX512=ON`, otherwise scalar arithmetic.
- `src/main.cpp`: prints one demonstration step and elapsed wall-clock nanoseconds.
- `python/aries_smart_answering.py`: request/response prototype with `/health` and `/v1/aries/query`.

## Important limitations
- The field names are illustrative. The operations are not Riemann zeta, Yang–Mills, or Navier–Stokes solvers and do not establish mathematical invariants.
- The API uses deterministic response templates. It does not load a trained LLM and does not invoke the C++ executable.
- The C++ timer measures elapsed wall-clock nanoseconds for one step. It does not establish sub-nanosecond latency; very short measurements are dominated by timer and scheduling overhead.
- AVX-512 builds require a compatible CPU at runtime. Enable with `-DARIES_ENABLE_AVX512=ON` only when the deployment hardware supports AVX-512.
- No build, runtime, API, or independent benchmark is claimed by this commit. Run CI and collect repeated samples before reporting performance.

## Local run
C++ (CMake 3.20+, C++20 compiler):
```sh
cmake -S . -B build
cmake --build build --config Release
./build/aries_gateway
```

Python:
```sh
python -m pip install fastapi uvicorn
python python/aries_smart_answering.py
```

The API is bound to localhost by default. Use a production server and explicit security configuration before exposing it publicly.
