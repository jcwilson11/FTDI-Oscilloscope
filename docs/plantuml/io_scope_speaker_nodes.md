# ioScope Diagram Speaker Nodes

This file collects speaker-ready note text for the professor-facing UML diagrams. Each section is written so it can be read directly during a presentation or adapted into PlantUML notes later.

## io_scope_logical_class_readable_mvc.puml

1. This diagram is the primary Qt MVC class slice. `ioOscilloscopeController` is the controller class, `ioOscilloscopeModel` is the model class, and `ioOscilloscopeView` is the single abstract View class for the Qt path.
2. The two selectable Qt user interfaces are modeled through inheritance. `ioCompactOscilloscopeView` and `ioDetailedOscilloscopeView` are concrete subclasses of the abstract class `ioOscilloscopeView`.
3. `ioQtScopeWindow` is a host-shell class, not a second View abstraction. It owns view-instance selection and visibility, then forwards user actions into the controller.
4. The model class aggregates state and processing context. `ioControlState` and `ioViewportState` hold user-facing state, while `ioFilterPipeline` and `ioWaveformGenerator` stay behind the model boundary.
5. The render handoff is made explicit through `ioRenderState`. That keeps rendering data separate from controller orchestration and helps the View layer stay presentation-focused.
6. The theme path is also an inheritance hierarchy. `ioViewTheme` is the abstract contract, `ioStaticThemeBase` is an abstract shared base, and `ioPortraitTheme` plus `ioLandscapeTheme` are concrete subclasses.
7. `ioLiveOscilloscopeSession` is attached to the controller rather than the View. That keeps live acquisition as application behavior instead of UI behavior.
8. `ioTkOscilloscopeWindow` is documented honestly as a legacy interface participant. It remains outside the primary Qt submission path.

## io_scope_logical_class_readable_signal_flow.puml

1. This class slice shows how live acquisition and waveform processing stay behind the MVC boundary. `ioOscilloscopeController` owns session startup and shutdown, while `ioOscilloscopeModel` owns waveform data and the active processing pipeline.
2. `ioLiveOscilloscopeSession` is the coordinating class for live acquisition. It owns the pipeline-related helper classes and keeps that behavior outside the View layer.
3. The filter design is modeled with both interface and inheritance terminology. `ioSignalFilter` is the interface, `ioSampleMappingFilterBase` is the abstract class for shared mapping logic, and `ioScaleFilter` plus `ioOffsetFilter` are concrete subclasses.
4. `ioFilterPipeline` depends on the filter interface rather than on one fixed concrete filter class. That means the processing chain is extensible without rewriting the pipeline class.
5. Source selection follows the same UML pattern. `ioSignalSource` is the interface, and `ioGeneratedWaveformSource`, `ioFileWaveformSource`, and `ioFtdiWaveformSource` are alternative concrete implementations.
6. `ioWaveformGenerator` acts as the selector for the active signal-source instance. It chooses which concrete source participates at runtime while the model stays at the abstraction level.
7. The byte-stream side is expressed through interfaces as well. `ioReadableByteStream` and `ioWritableByteStream` define the stream contracts, while helper classes such as `ioTappedReadableByteStream` and `ioNullWritableByteStream` participate around those abstractions.
8. `ioFtdiWaveformSource` is the concrete class that bridges signal acquisition into the FTDI stream layer by depending on `ioFtdiByteStream`.

## io_scope_logical_class_readable.puml

1. This is the top-level logical overview, so it is intentionally more architectural than class-by-class. The rounded rectangles are subsystem groupings rather than full detailed class declarations.
2. The bootstrap group contains the entry-point classes and verification helpers, including `ioScopeShell`, `ioPipelineCli`, `ioLegacyFtdiCli`, and `ioFileComparator`.
3. The Qt MVC group is the primary user-interface subsystem. Its detailed abstract-class and inheritance structure is intentionally moved into the companion MVC slice so this overview stays readable.
4. The signal-flow group and live-acquisition group are separated on purpose. One group handles waveform-processing strategy, while the other group handles live-session behavior and tee-history capture.
5. The transfer-pipeline group represents the required producer-consumer design. It connects the live acquisition subsystem to the FTDI stream subsystem through the multithreaded buffer path.
6. The FTDI streams and session group is the hardware-facing layer. It contains the deployed stream and device classes that the upper logical subsystems depend on.
7. The legacy operations group is isolated so grading can distinguish compatibility code from the current preferred architecture. It still depends on the FTDI stream layer, but it is not presented as the main path.
8. The dependency arrows communicate architectural direction between subsystems. They show who depends on whom, while the detailed class inheritance and interface realization relationships remain in the focused companion diagrams.

## io_scope_use_case.puml

1. This is the UML use-case view, so the focus is on externally visible system behavior rather than on internal class structure. The actor here is `Presenter`, which represents the person driving the demo.
2. The system boundary is the rectangle labeled `ioScope Demo`. Every use case inside that boundary is a user-visible capability that the system offers during demonstration or grading.
3. `Launch Qt oscilloscope` and `Launch CLI shell` are shown as separate use cases because the project supports both a Qt-facing path and a command-line path.
4. The Qt path is decomposed with `<<include>>` style relationships. Launching the Qt oscilloscope includes switching between the two Qt UIs, displaying the waveform, applying the scale and offset pipeline, and acquiring a waveform from FTDI.
5. `Switch between two Qt UIs` is a useful use case because it highlights a real architectural requirement: the system supports two concrete interface variants behind one shared View contract.
6. `Apply scale / offset pipeline` is modeled as a use case because signal transformation is user-visible behavior, even though it is implemented internally through filter classes and pipeline logic.
7. `Acquire waveform from FTDI` and `Run multithreaded FTDI pipeline` make the hardware and pipeline behavior visible at the requirements level. They show that the system is not only a static viewer but also an acquisition tool.
8. This diagram answers the question "what can the actor do with the system?" The class, process, and deployment diagrams answer the separate question of how those use cases are implemented.

## multithreaded_pipeline_activity.puml

1. This is a UML activity diagram, so it emphasizes control flow, decisions, concurrency, and termination conditions rather than static structure.
2. The activity starts in the `ioPipelineController` swimlane because that controller instance performs configuration, buffer creation, stream selection, and worker-thread startup.
3. The swimlanes separate responsibility by active participant. `ioPipelineController`, `ioUsbReadController`, `ioUsbWriteController`, and `ioDataBuffer` each own different parts of the workflow.
4. The `fork` node is important because it shows true concurrent behavior. After startup, the read controller activity and the write controller activity proceed in parallel.
5. The read-side branch models decision nodes for input mode and byte availability. It distinguishes file input from FTDI input and also distinguishes normal reads from exhaustion or failure conditions.
6. The buffer actions are shown explicitly as activity steps. `ioDataBuffer` waits on fullness or emptiness conditions, accepts pushed byte chunks from the producer side, and returns popped chunks to the consumer side.
7. The write-side branch models the consumer workflow. It repeatedly pops the next chunk, chooses the concrete destination path, and writes either to `ioFileByteStream` or `ioFtdiOutputByteStream`.
8. The end of the diagram shows coordinated shutdown activity. The pipeline controller requests stop, closes the shared buffer, waits for both worker threads to finish, and lets the writer close the selected output stream during stop.

## io_scope_process.puml

1. This is a UML process view, so the emphasis shifts from classes to concurrent runtime components. The diagram separates behavior by execution context instead of by inheritance hierarchy.
2. The `Qt UI Thread` rectangle contains the UI-facing component instances: the host window, the two concrete view components, the controller, the model, the live session, the pipeline controller, the filter pipeline, and the waveform generator.
3. The two background worker contexts are modeled explicitly as separate thread regions. `ioUsbReadController` lives in the read thread, and `ioUsbWriteController` lives in the write thread.
4. `ioDataBuffer` is drawn as a queue instance because it is the shared runtime handoff point between the producer and consumer threads. This is the concrete concurrent buffer instance that makes the pipeline work.
5. The controller component still acts as the orchestration center at runtime. It updates model state, starts and stops the live session, and dispatches rendering to the selected concrete Qt view component.
6. The process view makes one key architectural claim very visible: rendering and user interaction stay on the Qt UI thread, while continuous FTDI transfer work is pushed to background worker threads.
7. `ioQtScopeWindow` remains a host component even in the process view. It manages visibility of the two concrete view instances, but it does not become a second MVC View abstraction.
8. The read-side and write-side stream endpoints are modeled as runtime components behind the worker controllers. That keeps the thread roles clear: one side produces bytes into the queue, and the other consumes bytes out of it.

## io_scope_physical.puml

1. This is the UML physical or deployment view. The main concept here is not inheritance but deployment across nodes, artifacts, and external devices.
2. The `Windows Host` node contains the deployed software artifacts for the project: the Python runtime, the controller artifact, the oscilloscope package, the ioLibrary package, the Qt libraries, and the FTDI driver interface.
3. `io_scope_settings.json` is modeled as a database-style artifact because it persists runtime configuration, while the sample input is modeled as a file artifact because it represents an input resource rather than an executing component.
4. The `Display` node hosts the `Qt window` artifact. That makes the UI deployment boundary explicit and separates the visible interface from the host software stack.
5. The `USB Bus` node captures the hardware-facing side of the deployment. The FTDI read device is the primary external device artifact, and the FTDI write device is shown as an optional artifact for single-buffer transfer mode.
6. The deployment links show which host artifacts depend on which libraries and external endpoints. For example, the oscilloscope package depends on `PySide6`, `pyqtgraph`, settings storage, file input, and the visible UI artifact.
7. The ioLibrary package is the artifact that bridges software into the FTDI hardware layer. It depends on `ftd2xx.dll / D2XX` and communicates with the FTDI device artifacts on the USB bus.
8. This view is useful because it shows where runtime pieces exist physically: host machine, display target, and USB-connected devices. It complements the logical class view and the process view rather than replacing them.

## io_scope_use_case.puml

1. This is the UML use-case view, so the focus is on external goals rather than internal classes. The actor is the `Presenter`, and the system boundary is the `ioScope Demo` rectangle.
2. Each oval represents a user-visible capability of the system. The presenter can launch the Qt oscilloscope, launch the CLI shell, switch between the two Qt UIs, display a waveform, apply the scale-and-offset pipeline, acquire from FTDI, and run the multithreaded FTDI pipeline.
3. The use-case diagram stays intentionally high level. It does not show inheritance, controller classes, or thread structure because those belong to the class, process, and sequence views.
4. `Launch Qt oscilloscope` is the main interactive use case in this diagram. The included relationships show that launching the Qt path brings along UI switching, waveform display, pipeline application, and FTDI acquisition behavior.
5. `Launch CLI shell` is separated as its own use case because the project supports both the Qt presentation path and command-line entry points. That distinction matters for grading and demo setup.
6. `Switch between two Qt UIs` is modeled as a user-facing capability, not as an implementation detail. The use-case view communicates that the user can choose between two concrete interfaces without exposing the underlying abstract View class.
7. `Run multithreaded FTDI pipeline` is shown as a use case because the pipeline is not just a low-level helper; it is part of the demonstrable system behavior.
8. This diagram is useful as a requirements-facing summary. It answers what the presenter can do with the system before the other UML views explain how the architecture implements those goals.

## multithreaded_pipeline_activity.puml

1. This is a UML activity diagram, so the emphasis is on control flow, decisions, and concurrency instead of class inheritance. It describes the behavior of the multithreaded transfer pipeline from startup through shutdown.
2. The activity starts in `ioPipelineController`, which initializes the runtime context by parsing configuration, creating the `ioDataBuffer`, selecting the read-side and write-side stream implementations, and starting the worker threads.
3. The fork node is important because it marks true concurrent behavior. After startup, the read-side activity and the write-side activity run in parallel rather than as one serialized flow.
4. The `ioUsbReadController` swimlane represents the producer side of the pipeline. Its actions read byte chunks from either a file-backed source or an FTDI input source, then push those bytes into the shared buffer.
5. The `ioUsbWriteController` swimlane represents the consumer side. It waits for available data in `ioDataBuffer`, pops the next byte chunk, and writes that chunk to either a file output stream or an FTDI output stream.
6. The decision nodes make the runtime choices explicit: file versus FTDI input, file versus FTDI output, bytes returned versus source exhaustion, and full versus empty buffer conditions.
7. `ioDataBuffer` appears as the synchronization point between the two concurrent activities. In activity-diagram terms, it is the shared resource that coordinates the producer-consumer handoff.
8. The final control path returns to `ioPipelineController` for orderly shutdown. The controller requests stop, closes the shared buffer, joins the worker threads, and completes the activity only after both concurrent paths have been reconciled.
