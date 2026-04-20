# ioScope Qt MVC Architecture

## Design Summary
- The system uses MVC strictly: `ioOscilloscopeController` orchestrates, `ioOscilloscopeModel` stores state and processed data, and `ioOscilloscopeView` defines the render-only View boundary.
- The primary GUI path provides one abstract View boundary and two selectable concrete Qt user interfaces: `ioCompactOscilloscopeView` and `ioDetailedOscilloscopeView`.
- `ioQtScopeWindow` hosts those two concrete Qt view instances and controls which one is visible.
- Scale and offset remain in the pipe-and-filter path through `ioFilterPipeline`, `ioScaleFilter`, and `ioOffsetFilter`.
- Live acquisition runs through `ioLiveOscilloscopeSession`, which owns the multithreaded transfer pipeline and rolling sample history without collapsing MVC boundaries.
- FTDI communication remains isolated inside `ioLibrary`, with the oscilloscope consuming FTDI samples through `ioFtdiWaveformSource`.
- In the current implementation, controller, model, pipeline, and rendering all execute on the Qt UI thread.
- The required concurrent FTDI transfer path stays `ioUsbReadController -> ioDataBuffer -> ioUsbWriteController`.
- Legacy compatibility classes remain in the repository, but they are not part of the primary Qt submission path.

## Class Responsibilities

### Bootstrap And CLI
- `ioScopeShell`: Runs the interactive professor-facing shell and persists oscilloscope settings.
- `ioPipelineCli`: Builds pipeline configuration and runs the multithreaded FTDI/file transfer workflow.
- `ioLegacyFtdiCli`: Preserves the low-level FTDI demo commands for direct chip interaction.
- `ioFileComparator`: Compares binary files byte-for-byte for deterministic transfer verification.

### Qt MVC
- `ioOscilloscopeController`: Coordinates UI actions, model updates, and render fan-out.
- `ioOscilloscopeModel`: Stores raw samples, processed samples, control state, and viewport state.
- `ioOscilloscopeView`: Defines the abstract View contract for rendering and UI intent forwarding only.
- `ioCompactOscilloscopeView`: Implements the compact controls-first Qt interface.
- `ioDetailedOscilloscopeView`: Implements the detailed waveform-first Qt interface.
- `ioQtScopeWindow`: Hosts the selectable Qt views and forwards top-level UI selections to the controller.
- `ioOscilloscopeWindow`: Defines the legacy shell window protocol surface.
- `ioTkOscilloscopeWindow`: Preserves the older Tk shell window behavior outside the primary Qt path.
- `ioControlState`: Stores sample timing, source selection, FTDI settings, scale, offset, theme, and active view.
- `ioViewportState`: Stores the visible sample range configuration.
- `ioRenderState`: Carries immutable render data from the controller into each view.
- `ioScopeSettingsStore`: Loads and saves the oscilloscope runtime settings JSON payload.

### Live Session Support
- `ioLiveOscilloscopeSession`: Owns the live acquisition session and its tee-output pipeline.
- `ioLiveSampleHistory`: Stores rolling normalized samples for live rendering.
- `ioTappedReadableByteStream`: Mirrors live input bytes into sample history while preserving stream behavior.
- `ioLiveFileTailByteStream`: Tails a file as a continuously readable byte stream.
- `ioGeneratedWaveformByteStream`: Exposes generated demo waveforms as a readable byte stream.
- `ioNullWritableByteStream`: Discards tee output while preserving pipeline flow.

### Signal Pipeline
- `ioSignalFilter`: Defines the contract for one filter stage.
- `ioSampleMappingFilterBase`: Shares one-sample-at-a-time filter behavior.
- `ioScaleFilter`: Applies the vertical scale transform.
- `ioOffsetFilter`: Applies the vertical shift transform.
- `ioFilterPipeline`: Runs the configured filters in deterministic order.

### Signal Sources And Themes
- `ioSignalSource`: Defines the strategy contract for waveform acquisition.
- `ioGeneratedWaveformSource`: Produces deterministic generated demo waveforms.
- `ioFileWaveformSource`: Produces normalized samples from file input.
- `ioFtdiWaveformSource`: Produces normalized samples from FTDI device input.
- `ioWaveformGenerator`: Selects the active waveform source from control state.
- `ioViewTheme`: Defines the View theme contract.
- `ioStaticThemeBase`: Shares static theme metadata behavior.
- `ioPortraitTheme`: Supplies the portrait palette.
- `ioLandscapeTheme`: Supplies the landscape palette.

### FTDI Stream Hierarchy
- `ioFtdiDevice`: Provides the canonical FTDI device adapter over the session layer.
- `FtdiDevice`: Preserves the older compatibility alias over `ioFtdiDevice`.
- `ioLibraryError`: Defines the base runtime error for `ioLibrary`.
- `ioFtdiError`: Defines FTDI-specific library failures.
- `ioStreamLifecycle`: Defines stream open and close behavior.
- `ioReadableByteStream`: Defines read-side stream behavior.
- `ioWritableByteStream`: Defines write-side stream behavior.
- `ioAbstractReadableByteStream`: Shares readable-stream lifecycle and validation behavior.
- `ioAbstractWritableByteStream`: Shares writable-stream lifecycle and validation behavior.
- `ioAbstractSessionBackedByteStream`: Shares FTDI-session-backed stream behavior.
- `ioAbstractFileBackedByteStream`: Shares file-backed stream behavior.
- `ioFtdiByteStream`: Reads bytes from an FTDI device.
- `ioFtdiOutputByteStream`: Writes bytes to an FTDI device.
- `ioFileInputByteStream`: Reads bytes from a file.
- `ioFileByteStream`: Writes bytes to a file.
- `ioFtdiSession`: Owns the D2XX session boundary.

### Multithreaded Transfer Pipeline
- `ioPipelineConfig`: Stores end-to-end transfer settings.
- `ioAcquisitionConfig`: Stores read worker settings.
- `ioTransferConfig`: Stores write worker settings.
- `ioPipelineController`: Builds and coordinates the transfer workers and shared buffer.
- `ioDataBuffer`: Implements the required thread-safe bounded circular buffer.
- `ioByteCountMonitorBase`: Shares byte-count and throughput timing behavior.
- `ioThreadedWorkerBase`: Shares worker thread lifecycle behavior.
- `ioAbstractThreadedStreamWorker`: Shares threaded stream worker behavior.
- `ioUsbReadController`: Reads bytes from a stream and pushes them into the circular buffer.
- `ioUsbWriteController`: Pops bytes from the circular buffer and writes them to a stream.
- `ioRecoveryManager`: Coordinates safe-stop error handling across worker threads.
- `ioAcquisitionMonitor`: Tracks read counts and throughput.
- `ioThroughputMonitor`: Tracks write counts and throughput.
- `ioRateSchedulerBase`: Shares scheduling behavior for fixed-rate loops.
- `ioInputScheduler`: Applies read-side timing policy.
- `ioOutputScheduler`: Applies write-side timing policy.

### Legacy Compatibility Operations
- `ioBuffer`: Preserves the older fixed-size buffer abstraction used by the original operation classes.
- `ioBaseIoOperation`: Shares the legacy timed FTDI operation behavior.
- `ioRead`: Implements the legacy FTDI read operation over `ioBuffer`.
- `ioWrite`: Implements the legacy FTDI write operation over `ioBuffer`.

## Required Relationships
- `ioCompactOscilloscopeView` inherits `ioOscilloscopeView`.
- `ioDetailedOscilloscopeView` inherits `ioOscilloscopeView`.
- `ioQtScopeWindow` hosts concrete instances of `ioCompactOscilloscopeView` and `ioDetailedOscilloscopeView`.
- `ioOscilloscopeController` owns one `ioLiveOscilloscopeSession` for live acquisition mode.
- `ioLiveOscilloscopeSession` owns one `ioPipelineController` and one `ioLiveSampleHistory`.
- `ioTappedReadableByteStream` decorates one readable stream and appends into `ioLiveSampleHistory`.
- `ioScaleFilter` and `ioOffsetFilter` inherit `ioSampleMappingFilterBase`.
- `ioSampleMappingFilterBase` implements `ioSignalFilter`.
- `ioGeneratedWaveformSource`, `ioFileWaveformSource`, and `ioFtdiWaveformSource` implement `ioSignalSource`.
- `ioFtdiByteStream` and `ioFileInputByteStream` inherit the readable stream hierarchy.
- `ioFtdiOutputByteStream` and `ioFileByteStream` inherit the writable stream hierarchy.
- `ioFtdiDevice` inherits `ioFtdiSession`.
- `ioUsbReadController` and `ioUsbWriteController` inherit `ioAbstractThreadedStreamWorker`.
- `ioAcquisitionMonitor` and `ioThroughputMonitor` inherit `ioByteCountMonitorBase`.
- `ioRead` and `ioWrite` inherit `ioBaseIoOperation`.

## 4+1 Artifact Set
- Logical overview: [io_scope_logical_class.puml](../plantuml/io_scope_logical_class.puml)
- Logical MVC slice: [io_scope_logical_class_mvc.puml](../plantuml/io_scope_logical_class_mvc.puml)
- Logical signal-flow slice: [io_scope_logical_class_signal_flow.puml](../plantuml/io_scope_logical_class_signal_flow.puml)
- Logical FTDI-stream slice: [io_scope_logical_class_ftdi_streams.puml](../plantuml/io_scope_logical_class_ftdi_streams.puml)
- Logical transfer-pipeline slice: [io_scope_logical_class_transfer_pipeline.puml](../plantuml/io_scope_logical_class_transfer_pipeline.puml)
- Logical readable overview: [io_scope_logical_class_readable.puml](../plantuml/io_scope_logical_class_readable.puml)
- Logical readable MVC slice: [io_scope_logical_class_readable_mvc.puml](../plantuml/io_scope_logical_class_readable_mvc.puml)
- Logical readable signal-flow slice: [io_scope_logical_class_readable_signal_flow.puml](../plantuml/io_scope_logical_class_readable_signal_flow.puml)
- Logical readable FTDI-stream slice: [io_scope_logical_class_readable_ftdi_streams.puml](../plantuml/io_scope_logical_class_readable_ftdi_streams.puml)
- Logical readable transfer-pipeline slice: [io_scope_logical_class_readable_transfer_pipeline.puml](../plantuml/io_scope_logical_class_readable_transfer_pipeline.puml)
- Process view: [io_scope_process.puml](../plantuml/io_scope_process.puml)
- Development overview: [io_scope_development.puml](../plantuml/io_scope_development.puml)
- Development bootstrap/MVC slice: [io_scope_development_bootstrap_mvc.puml](../plantuml/io_scope_development_bootstrap_mvc.puml)
- Development signal/live slice: [io_scope_development_signal_live.puml](../plantuml/io_scope_development_signal_live.puml)
- Development ioLibrary streams slice: [io_scope_development_iolibrary_streams.puml](../plantuml/io_scope_development_iolibrary_streams.puml)
- Development ioLibrary pipeline slice: [io_scope_development_iolibrary_pipeline.puml](../plantuml/io_scope_development_iolibrary_pipeline.puml)
- Physical view: [io_scope_physical.puml](../plantuml/io_scope_physical.puml)
- Scenario view: [io_scope_scenario_sequence.puml](../plantuml/io_scope_scenario_sequence.puml)
- Package overview: [io_scope_package.puml](../plantuml/io_scope_package.puml)

## Implementation Notes
- `scope-qt` is the primary GUI entrypoint.
- `scope-shell` remains a CLI verification harness.
- `oscilloscope/view.py`, `oscilloscope/model.py`, `oscilloscope/controller.py`, and `oscilloscope/filters.py` are compatibility re-export modules rather than primary implementation files.
- `origin/oscilloscope` contains the earlier simplified scaffold and is historical source material rather than the canonical submission architecture.
- The Qt modules import gracefully when `PySide6` or `pyqtgraph` are unavailable so the non-GUI tests can still run.
- The extra-credit two-device design remains an extension on top of the single-buffer required path.

## Documentation History
- Initial state: Tk-oriented oscilloscope demo with two composed concrete view instances.
- Current state: abstract `ioOscilloscopeView`, two selectable concrete Qt views, one `ioQtScopeWindow`, explicit live-session classes, canonical `ioFtdiDevice` naming, and logical diagrams that include the implemented live-session and legacy classes.
- Preserved design decision: scale and offset still run only through the filter pipeline, and FTDI transfer still uses the multithreaded circular buffer path in `ioLibrary`.
