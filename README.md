# FTDI-Oscilloscope

## Overview
This repository contains the initial development work for a PC-based oscilloscope application that interfaces with FTDI hardware. The goal of this project is to design and implement a digital oscilloscope capable of real-time visualization and analysis of electrical signals.

As part of the system architecture process, an initial **user interface prototype** was created using Figma. This prototype represents the planned layout and functionality of the oscilloscope control software.


## Figma User Interface Design

The oscilloscope interface was designed using **Figma** to prototype the layout before implementing the software.

The Figma design includes:

- Waveform selection (Sine, Square, Triangle, Sawtooth)
- Frequency control
- Amplitude adjustment
- Signal offset adjustment
- Time/div control
- Trigger level adjustment
- Run and Reset control buttons

This layout describes the planned structure of the oscilloscope control software.

### Figma Design Link

View the full design here:

https://www.figma.com/design/X6zNvyLg22J7tkcQIDl1BI/Oscilloscope-Wireframe?node-id=0-1&t=w9TdjTskqkcVeDE0-1

The Figma file contains the wireframes and UI layout used for the initial system architecture design.



## User Interface Description

The oscilloscope interface is divided into functional sections:

### Channel Configuration Panels
Each channel panel allows the user to configure the waveform signal for that channel.

Each channel is color coded for clarity when visualized in the oscilloscope display.

### Oscilloscope Controls
The oscilloscope control section provides controls for the signal visualization.

Controls include:
- Time per division (Time/Div)
- Trigger level adjustment
- Run button to start signal generation
- Reset button to restore default settings

### Oscilloscope Display
The oscilloscope display area shows the generated waveforms for both channels. The interface supports simultaneous visualization of multiple signals to allow comparison and signal analysis.



## Purpose of the UI Prototype

The Figma prototype was created to:

- Plan the oscilloscope software layout
- Define user interaction workflows
- Establish the control structure for signal generation
- Provide a reference for future implementation

This design helps guide the development of the oscilloscope software interface before integrating the hardware signal acquisition system.

## Figma UI Screenshots

Below are screenshots of the oscilloscope interface prototype created in Figma.

### Oscilloscope Display

<img width="1440" height="1024" alt="Oscilloscope UI" src="https://github.com/user-attachments/assets/9e7c3617-96f3-4c28-9215-d1b90fb50d4c" />

### Channel Control Panels

<img width="954" height="682" alt="Control Panel UI" src="https://github.com/user-attachments/assets/5c2257b0-85ef-4250-b00b-607308eb2b04" />

## Future Development

Future updates to this project will include:

- Implementation of the oscilloscope interface in software
- Integration with FTDI hardware
- Real-time signal acquisition and visualization

## Current Python Architecture Work

The repository now includes a reusable Python package named `ioLibrary` for FTDI input/output responsibilities. This package separates hardware communication from the application layer so small demo programs and later oscilloscope features can reuse the same FTDI handling code.

Current architecture additions:

- `ioLibrary.ioBuffer` manages reusable byte buffers
- `ioLibrary.ioRead` reads bytes from the FTDI device into an external buffer at a configured frequency
- `ioLibrary.ioWrite` writes bytes from an external buffer at a configured frequency
- `ioLibrary.ioStreamLifecycle`, `ioReadableByteStream`, and `ioWritableByteStream` make the stream contracts explicit
- `ioAbstractReadableByteStream` and `ioAbstractWritableByteStream` centralize the shared `read_bytes` and `write_bytes` responsibilities across file and FTDI adapters
- `ioAbstractSessionBackedByteStream` and `ioAbstractFileBackedByteStream` centralize duplicated stream lifecycle behavior
- `ioThreadedWorkerBase`, `ioRateSchedulerBase`, and `ioByteCountMonitorBase` centralize duplicated worker, scheduler, and monitor behavior
- `demo_led_blink.py` demonstrates LED blinking with `0xFF` and `0x00` at 1 Hz and 2 Hz
- `oscilloscope/` contains the MVC user interface and Pipe-and-Filter signal processing redesign, including `ioOscilloscopeWindow`, `ioStaticThemeBase`, `ioSampleMappingFilterBase`, and signal-source strategies behind `ioWaveformGenerator`
- `oscilloscope/io_live_oscilloscope_session.py` keeps live acquisition, tee output, and rolling sample history separate from the MVC View classes
- `ioLibrary.pipeline.PipelineController` coordinates the multithreaded FTDI read -> circular buffer -> write pipeline
- `controller.py pipeline` provides a command-line entrypoint for the multithreaded pipeline

## Multithreaded Pipeline Usage

The repository now includes a multithreaded FTDI data acquisition pipeline. The pipeline reads bytes from an FTDI source device, stores them in a thread-safe circular buffer, and writes them either to a file or to another FTDI device.

The pipeline can also be run in a deterministic file-to-file demo mode, which reads bytes from an input file, pushes them through the same shared buffer, and writes them back out to an output file.

### Requirements

Before running the pipeline, make sure the following are true:

- Windows is being used
- Python is installed
- The FTDI D2XX driver is installed
- `ftd2xx.dll` is available on `PATH`, or you know its full path
- At least one FTDI device is connected for file output mode
- Two FTDI devices are connected for FTDI-to-FTDI mode

### Device Discovery

List the FTDI devices visible through the D2XX driver:

```powershell
python controller.py --list-devices
```

Expected result:

- One line per FTDI device
- Each line includes the device `index`, `serial`, `description`, `id`, `location`, and `flags`

Example:

```text
index=0 serial=FT123456 description=USB <-> Serial Converter id=0x00000000 location=0x00000000 flags=0x00000002
```

Use the reported `index` value as `--input-device-index` or `--output-device-index`.

### Basic Commands

Run the pipeline from an FTDI device to a file:

```powershell
python controller.py pipeline --output-mode file --output-path demo_output.bin --input-device-index 0 --bytes-per-read 8 --bytes-per-write 8 --input-hz 20 --output-hz 20 --buffer-capacity 256 --duration-seconds 5
```

Run the pipeline from a file to a file for a repeatable round-trip test:

```powershell
python controller.py pipeline --input-mode file --input-path demo_input.bin --output-mode file --output-path demo_output.bin --overwrite-output --bytes-per-read 8 --bytes-per-write 8 --input-hz 20 --output-hz 20 --buffer-capacity 256 --duration-seconds 5
```

Then compare the result against the original input:

```powershell
python controller.py compare-files demo_input.bin demo_output.bin
```

Run the pipeline from one FTDI device to another FTDI device:

```powershell
python controller.py pipeline --output-mode ftdi --input-device-index 0 --output-device-index 1 --bytes-per-read 8 --bytes-per-write 8 --input-hz 20 --output-hz 20 --buffer-capacity 256 --duration-seconds 5
```

If `ftd2xx.dll` is not on `PATH`, pass it explicitly before the `pipeline` subcommand:

```powershell
python controller.py --dll "C:\path\to\ftd2xx.dll" pipeline --output-mode file --output-path demo_output.bin --input-device-index 0 --duration-seconds 5
```

### Pipeline Arguments

The multithreaded pipeline is started with:

```powershell
python controller.py pipeline [arguments]
```

| Argument | Required | Valid values / range | Purpose | Expected result |
| --- | --- | --- | --- | --- |
| `--input-mode` | No | `file` or `ftdi` | Selects the read source type | File mode reads from a file, FTDI mode reads from an FTDI device |
| `--input-device-index` | No | Integer `>= 0` | Selects the FTDI source device index for the read thread | The read thread reads from the chosen FTDI device |
| `--input-path` | Yes for `file` mode | Readable file path | Input file source for file mode | Bytes are read from the selected file |
| `--output-mode` | Yes | `file` or `ftdi` | Selects the write destination type | File mode writes to a file, FTDI mode writes to another FTDI device |
| `--output-path` | Yes for `file` mode | Writable file path | Output file destination for file mode | Bytes are appended to the selected file |
| `--output-device-index` | Yes for `ftdi` mode | Integer `>= 0` | Selects the FTDI destination device index for FTDI output mode | The write thread writes to the chosen FTDI device |
| `--overwrite-output` | No | Flag | Replaces the output file instead of appending to it | Makes file-to-file comparisons repeatable |
| `--bytes-per-read` | No | Integer `> 0` | Number of bytes requested from the FTDI source each read loop | Larger values read larger chunks each cycle |
| `--bytes-per-write` | No | Integer `> 0` | Maximum number of bytes written from the circular buffer each write loop | Larger values write larger chunks each cycle |
| `--input-hz` | No | Float `> 0` | Read loop frequency in Hertz | Controls how often the read loop runs |
| `--output-hz` | No | Float `> 0` | Write loop frequency in Hertz | Controls how often the write loop runs |
| `--buffer-capacity` | No | Integer `> 0`, must be at least `max(bytes-per-read, bytes-per-write)` | Size of the shared circular buffer in bytes | Larger values allow more mismatch between read and write rates |
| `--duration-seconds` | No | Float `> 0` | How long the pipeline runs before clean shutdown | The program stops automatically after the requested time |

Current defaults:

- `--input-mode ftdi`
- `--input-device-index 0`
- `--bytes-per-read 8`
- `--bytes-per-write 8`
- `--input-hz 10.0`
- `--output-hz 10.0`
- `--buffer-capacity 1024`
- `--duration-seconds 2.0`

### Top-Level Controller Arguments

These arguments are supported by the existing controller entrypoint outside the pipeline mode:

| Argument | Valid values / range | Purpose |
| --- | --- | --- |
| `--dll` | Valid file path | Explicit path to `ftd2xx.dll` |
| `--list-devices` | Flag | Lists visible FTDI devices and exits |
| `--write` | Integer from `0` to `255`, decimal or hex | Writes one byte to the FTDI device and exits |
| `--read` | Flag | Reads one byte from the FTDI device and exits |
| `--morse` | Any text string | Sends Morse-code timing patterns to the FTDI device |

### Validation Rules

The pipeline validates the following before it starts:

- `--input-mode` must be `file` or `ftdi`
- `--output-mode` must be `file` or `ftdi`
- `--duration-seconds` must be greater than `0`
- `--bytes-per-read` must be greater than `0`
- `--bytes-per-write` must be greater than `0`
- `--input-hz` must be greater than `0`
- `--output-hz` must be greater than `0`
- `--buffer-capacity` must be greater than `0`
- `--buffer-capacity` must be at least the larger of the read and write chunk sizes
- `file` mode input requires `--input-path`
- `file` mode requires `--output-path`
- `ftdi` mode requires `--output-device-index`

### Expected Output

When the pipeline finishes, it prints a summary similar to this:

```text
Pipeline stopped.
Output mode: file
Bytes read: 128
Bytes written: 128
Read throughput KB/s: 0.625
Write throughput KB/s: 0.621
Buffer size: 0
Recovery safe stop: False
```

What each field means:

- `Output mode`: destination type that was used
- `Bytes read`: total bytes acquired by the read thread
- `Bytes written`: total bytes written by the write thread
- `Read throughput KB/s`: measured read-side throughput
- `Write throughput KB/s`: measured write-side throughput
- `Buffer size`: bytes left in the circular buffer when the run ended
- `Recovery safe stop`: `True` if a read or write failure forced a safe-stop path

Expected successful results:

- In file mode, the output file exists and contains the transferred bytes
- In file-to-file mode, `demo_input.bin` and `demo_output.bin` can be compared directly
- In FTDI mode, the destination FTDI device receives the byte stream
- `Bytes read` and `Bytes written` are both nonzero for an active data source
- `Buffer size` is normally `0` after a clean stop
- `Recovery safe stop` is normally `False`

### File Output Verification

After running file mode, you can inspect the output file:

```powershell
Get-Item demo_output.bin
```

To view the raw bytes:

```powershell
Format-Hex demo_output.bin
```

To compare an output file against a reference file byte-for-byte:

```powershell
python controller.py compare-files demo_output.bin reference_output.bin
```

Expected result:

- Exit code `0` when both files are identical
- Exit code `1` when the files differ or one of the paths is invalid
- A message showing either an exact match or the first differing byte offset

### Recommended Starting Values

For a first test, start with file mode and moderate settings:

- `--bytes-per-read 8`
- `--bytes-per-write 8`
- `--input-hz 20`
- `--output-hz 20`
- `--buffer-capacity 256`
- `--duration-seconds 5`

Why these values are a good starting point:

- Small chunk sizes are easier to reason about
- Moderate loop rates reduce timing stress while testing
- A `256` byte buffer is large enough to absorb short mismatches between read and write speed
- A 5 second run is enough to verify that the pipeline starts, transfers data, and shuts down cleanly

### Troubleshooting

Problem: `No FTDI devices visible through the D2XX driver.`

- The FTDI device may not be connected
- The D2XX driver may not be installed
- The wrong driver may be bound to the device

Problem: `Could not load ftd2xx.dll`

- Pass the DLL explicitly with `--dll`
- Confirm the DLL path is correct

Problem: `file output mode requires output_path`

- Add `--output-path`

Problem: `ftdi output mode requires output_device_index`

- Add `--output-device-index`

Problem: `buffer_capacity must be at least the largest chunk size`

- Increase `--buffer-capacity`
- Or reduce `--bytes-per-read` / `--bytes-per-write`

Problem: `Recovery safe stop: True`

- A read or write error occurred
- Check the terminal output for recovery messages
- Verify device connections and FTDI indices

### Notes

- File mode is the easiest path for demonstration and verification
- The circular buffer implementation is `DataBuffer` in `ioLibrary.data_buffer`
- The end-to-end pipeline coordinator is `PipelineController` in `ioLibrary.pipeline`
- The command-line pipeline entrypoint is `controller.py pipeline`

### Testing

Run the automated test suite from the repository root:

```powershell
pytest -q
```

The repository includes `tests/conftest.py`, which inserts the project root onto `sys.path` so the tests can import `ioLibrary` and `controller` without requiring a manual `PYTHONPATH` step.

## Oscilloscope Qt Demo

The repository now includes a professor-facing Qt oscilloscope architecture built around one abstract View contract and two selectable concrete Qt interfaces.

Canonical class names follow the `io<ClassName>` rule.
Legacy names remain only as thin compatibility aliases where needed.

Compile check:

```powershell
python -m compileall controller.py io_scope_qt.py io_scope_shell.py ioLibrary oscilloscope tests
```

Verification:

```powershell
pytest -q
```

Run the Qt oscilloscope entrypoint:

```powershell
python controller.py scope-qt --headless
```

Run the shell verification harness:

```powershell
python controller.py scope-shell
```

Supported shell commands:

```text
scope start
sampleTime=1ms
sampleFor=10s
input=sine
input=file:demo_input.bin
scale=2.0
offset=0.25
theme=portrait
theme=landscape
status
stop
```

Runtime settings are persisted in `io_scope_settings.json` at the repository root, so scale, offset, theme, input source, FTDI settings, and active view survive between sessions.

Supporting architecture documents:

- `docs/io_project_requirements.md`
- `docs/architecture/io_qt_mvc_architecture.md`
- `docs/ai_prompt_and_output.md`
- `docs/traceability_matrix.md`
- `docs/plantuml/io_scope_package.puml`
- `docs/plantuml/io_scope_logical_class.puml`
- `docs/plantuml/io_scope_logical_class_readable.puml`
- `docs/plantuml/io_scope_process.puml`
- `docs/plantuml/io_scope_development.puml`
- `docs/plantuml/io_scope_physical.puml`
- `docs/plantuml/io_scope_scenario_sequence.puml`
- `docs/plantuml/io_scope_use_case.puml`
- `docs/plantuml/io_scope_deployment.puml`
- `docs/plantuml/io_scope_runtime_component.puml`
- `docs/plantuml/io_scope_object.puml`
- `docs/plantuml/io_scope_start_sequence.puml`
- `docs/plantuml/io_scope_controls_sequence.puml`

