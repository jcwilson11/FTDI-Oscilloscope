# Multithreaded Data Acquisition Pipeline

This chapter describes the implemented multithreaded pipeline for the FTDI assignment. The runtime path is FTDI input device -> `UsbReadController` -> `DataBuffer` -> `UsbWriteController` -> `FileByteStream` or `FtdiOutputByteStream`. The chapter uses the concrete repository class names as the primary architectural vocabulary and notes the assignment roles as secondary labels.

## Overview

The repository now includes the integrated pipeline coordinator in `ioLibrary.pipeline.PipelineController` in addition to the multithreaded read and write building blocks in `ioLibrary`, including `UsbReadController`, `UsbWriteController`, `DataBuffer`, `WritableByteStream`, `FileByteStream`, `FtdiOutputByteStream`, `FtdiByteStream`, and `FtdiSession`. `DataBuffer` now lives in `ioLibrary.data_buffer` because it is a shared synchronization abstraction used by both workers rather than a detail of the write side alone. The UML keeps these concrete names front and center so the diagrams can be verified directly against the code.

The current refactor also makes the interface and inheritance boundaries explicit. `ioStreamLifecycle` now holds the common `open()` / `close()` / `is_connected()` contract, `ioReadableByteStream` and `ioWritableByteStream` extend that protocol for direction-specific byte access, and the concrete FTDI and file adapters inherit shared abstract base classes for duplicated lifecycle behavior. The worker, scheduler, and monitor layers follow the same pattern so the repository uses protocols for replaceable collaborators and abstract base classes only where real shared behavior exists.

## Integrated Pipeline Design

- `PipelineController` configures the pipeline, starts both worker threads, coordinates shutdown, and reports runtime status to the command-line layer.
- `UsbReadController` acquires data from the FTDI input device and acts as the producer side of the pipeline.
- `DataBuffer` provides bounded, thread-safe transfer between the producer and consumer threads.
- `UsbWriteController` removes data from the circular buffer and forwards it to the selected output destination.
- `WritableByteStream` abstracts the destination so the write side can target either a file or another FTDI device.

The primary documented path is FTDI-to-file, because that is the clearest demonstration path for the current assignment stage. The same write-side structure also supports FTDI-to-FTDI transfer as an alternate destination.

## Circular Buffer Design

The circular buffer is the core of the producer-consumer design. Its responsibilities are:

- fixed capacity to keep memory usage bounded
- blocking `push()` when the buffer is full
- blocking `pop()` when the buffer is empty
- separate producer and consumer positions
- a closed state that supports coordinated shutdown and final draining

In the implementation, this role is handled by `DataBuffer` in `ioLibrary.data_buffer`. The class uses circular-buffer internals with bounded ring storage, blocking `push()` and `pop()`, explicit close semantics for coordinated shutdown, and tests that cover wake-up behavior for both blocked producers and blocked consumers.

## Architectural Relationships and Ownership

The design is clearer when the relationships are described explicitly:

- `PipelineController` has a composition relationship to `UsbReadController`, `UsbWriteController`, and `DataBuffer`. It creates them, starts them, stops them, and they do not have an independent architectural lifetime outside a single pipeline run.
- `PipelineController` has a 1-to-1 aggregation relationship to one selected `WritableByteStream` implementation during the run. In the class diagram this is the open-diamond relationship: the controller keeps a reference to the selected sink strategy, but the sink remains a replaceable collaborator rather than a tightly composed subpart.
- `UsbReadController` and `UsbWriteController` each have an ordinary shared association with `DataBuffer`, not composition. They both depend on the same buffer instance, but neither one owns the buffer's lifetime. That distinction is important because the buffer is the synchronization boundary between the producer and consumer threads.
- `WritableByteStream` is an interface/protocol contract. `FileByteStream` and `FtdiOutputByteStream` realize that contract, while inheriting shared lifecycle behavior from abstract file-backed and session-backed stream base classes. No multiplicity belongs on these realization relationships because multiplicity is used on associations, not on interface inheritance.
- `ReadableByteStream` and `WritableByteStream` both extend `StreamLifecycle`, which captures the common lifecycle boundary without forcing read and write collaborators into the same concrete inheritance tree.
- `FtdiByteStream` and `FtdiOutputByteStream` each compose an `FtdiSession` through `ioAbstractSessionBackedByteStream`. The stream wrappers create, use, and close the session as part of their own lifecycle, so the session does not escape as an independently managed architectural object.

These relationship choices are not just diagram notation. They explain why the design stays maintainable: synchronization is centralized in one shared buffer, hardware access is localized behind stream wrappers, and destination-specific behavior is isolated behind a protocol boundary.

## Data Flow

1. `controller.py pipeline` parses the source device, destination type, chunk size, duration, and buffer capacity.
2. `PipelineController` creates `DataBuffer` and selects the `WritableByteStream` implementation.
3. `PipelineController` starts `UsbWriteController` and then `UsbReadController`.
4. `UsbReadController` acquires bytes from the FTDI input side and pushes them into `DataBuffer`.
5. `UsbWriteController` pops available bytes from `DataBuffer` and writes them to the selected sink.
6. On shutdown, the controller stops the producer, closes the buffer, and requests the consumer to stop.
7. The write side drains remaining data before its loop exits, retries partial sink writes until the current chunk has been fully flushed, and closes the selected output stream in its own shutdown finalization path rather than relying on the controller to close that resource directly.

The startup order is intentional. `PipelineController` starts `UsbWriteController` before `UsbReadController` so the consumer is already waiting on the buffer before the producer begins filling it. That reduces avoidable startup backlog and makes the producer-consumer handoff cleaner.

## Repository Mapping

| UML Name | Current Prototype Mapping |
| --- | --- |
| `UsbReadController` | `UsbReadController` |
| `UsbWriteController` | `UsbWriteController` |
| `PipelineController` | `ioLibrary.pipeline.PipelineController` |
| `DataBuffer` | `DataBuffer` |
| `WritableByteStream` | `FileByteStream` or `FtdiOutputByteStream` |
| `FileByteStream` | `FileByteStream` |
| `FtdiOutputByteStream` | `FtdiOutputByteStream` |
| `FTDI input stream` | `FtdiByteStream` |
| `FTDI output stream` | `FtdiOutputByteStream` |
| `FtdiSession` | `FtdiSession` |

## UML Diagrams

### Read-Side Component Diagram

Source: `docs/plantuml/multithreaded_pipeline_read_component.puml`

Shows the read-side software components and the top-level flow between the CLI, controller, read worker, circular buffer, and selected input source.

### Write-Side Component Diagram

Source: `docs/plantuml/multithreaded_pipeline_write_component.puml`

Shows the write-side software components and the top-level flow between the CLI, controller, write worker, circular buffer, selected output sink, and validation files.

### Class Diagram

Source: `docs/plantuml/multithreaded_pipeline_class.puml`

Shows the responsibilities of the main classes with the concrete repository names as the primary labels and the assignment roles as stereotypes or notes.

### Sequence Diagram

Source: `docs/plantuml/multithreaded_pipeline_sequence.puml`

Shows startup, steady-state data transfer, alternate file or FTDI output flow, coordinated shutdown, and full-chunk flushing on partial sink writes.

### Activity Diagram

Source: `docs/plantuml/multithreaded_pipeline_activity.puml`

Shows the producer-consumer runtime behavior, including buffer-full waits, buffer-empty waits, and controlled stop behavior.
