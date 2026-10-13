# Architecture and interview notes

## Components and boundaries

`src/cv/detector.py` owns preprocessing, ONNX execution, and output decoding. It does not
know about HTTP. `src/api/main.py` owns payload validation, error mapping, admission
control, health, and metrics. `src/cv/video.py` owns capture, buffering, retries, and
output. The export and benchmark commands run separately from serving.

A small project does not need repository/service abstractions for every function.
The separation follows reasons to change: model format, transport, source capture,
and release process. The concrete detector can be replaced at the application boundary.

## Concurrency and backpressure

The API reads request bodies asynchronously, with two admission slots by default.
Slots remain held until decoding and inference finish. CPU work runs in the Starlette
thread pool. ONNX Runtime uses two intra-op threads and one inter-op thread per session.
More API workers each load a separate session and have separate admission limits and
metrics; deployment must account for total memory and CPU usage.

The client has one producer thread and one consumer. OpenCV frame acquisition and HTTP
requests can wait on different I/O, so capture is decoupled from inference. This is not
proof that pure Python CPU work scales with threads. Dropping stale queued frames keeps
memory bounded and favors current results; it sacrifices complete frame coverage.

The consumer removes a frame before sending it. Frame age includes JPEG encoding,
network delay, server work, and retries. For archival processing where every frame
matters, use a separate blocking queue policy and do not discard frames.

## Reliability

- Checksum verification catches accidental model/manifest mismatch. It is not a signature.
- Liveness and readiness have separate meanings.
- One ONNX session is immutable for the process lifetime. Model updates require restart.
- `429` explicitly signals overload. Clients retry only bounded transient failures.
- The selected release should be pinned by image digest for deployment.
- VideoCapture may block on an unreachable source; the reader join has a timeout and
  surfaces this limitation. Stream reconnection and per-backend timeouts remain future work.
- HTTP does not guarantee a real-time deadline. Measured latency and dropping policy
  define the demo behavior; no production real-time SLA is claimed.

## Model lifecycle

1. Download official pretrained checkpoint once; keep its source hash.
2. Export to static ONNX and compare raw outputs to PyTorch on a seeded probe.
3. Store model, labels, hashes, export parameters and versions together in a release directory.
4. DVC tracks release artifacts; Git tracks pipeline and code. This repo has no configured
   remote DVC storage, so cross-machine cache recovery needs a configured remote or re-export.
5. Benchmark the selected release on target hardware.
6. Build image, validate model at build time, run readiness and HTTP smoke tests.
7. Publish a tagged release; deploy selected tag/digest and retain prior image for rollback.

Probe parity catches export errors. It does not establish mAP or task-specific model
quality. No automatic training, drift-triggered retraining, or model registry is present.
Adding MLflow merely to list another technology would not resolve these gaps.

## Interview discussion prompts

- Why use a latest-frame queue? What changes for offline processing?
- What happens when five clients send frames faster than the server can infer?
- What is the difference between multithreading, multiprocessing, and async I/O here?
- Why normalize RGB input but capture BGR? How are boxes mapped through letterboxing?
- Why apply NMS per class, and what does its IoU threshold mean?
- What does the ONNX parity check establish, and what must be evaluated on real data?
- What limits should change when adding workers, GPU inference, or multiple video sources?
- How would you detect a broken release, roll it back, and compare hardware performance?
