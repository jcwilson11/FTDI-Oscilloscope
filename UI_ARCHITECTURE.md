# UI Architecture

## Responsibilities

- `ioViewBase`
  Defines the abstract View contract for MVC. Controllers can call `updateSignal(signalData)` and bind themselves through `connectController(controller)`. Implementations do not perform FTDI I/O, file input, or waveform processing.

- `ioOscilloscopeViewDark`
  Active Qt View implementation that renders oscilloscope data in a dark theme using `pyqtgraph`. It does not fetch or transform data.

- `ioOscilloscopeViewLight`
  Active Qt View implementation that renders oscilloscope data in a light theme using `pyqtgraph`. It does not fetch or transform data.

- `ioMainWindow`
  Active Qt UI shell for the assignment. It hosts the selectable views in a stacked widget, forwards controller-provided waveform updates to the active view, and emits user selections for theme and data source to the controller.

- `OscilloscopeView`
  Legacy compatibility wrapper kept only for older scaffolding imports. It is not the primary UI for this assignment.

## UI Requirements Coverage

- Qt-based implementation using `PySide6`
- Two selectable View implementations
- Minimal oscilloscope interface centered on waveform display
- Minimal controls limited to theme selection and data source selection
- MVC-safe View abstraction with no FTDI, pipeline, or business logic in the UI
- Real-time plotting through `pyqtgraph`
- Data-source selection emits a UI event to the controller

## Class Diagram

```mermaid
classDiagram
    class ioViewBase {
        +updateSignal(signalData)
        +connectController(controller)
    }

    class ioOscilloscopeViewDark {
        -_controller
        -_plotWidget
        -_curve
        -_lastSignal
        +updateSignal(signalData)
        +connectController(controller)
    }

    class ioOscilloscopeViewLight {
        -_controller
        -_plotWidget
        -_curve
        -_lastSignal
        +updateSignal(signalData)
        +connectController(controller)
    }

    class ioMainWindow {
        +dataSourceChanged
        +themeChanged
        -_controller
        -_darkView
        -_lightView
        -_stack
        -_themeSelector
        -_sourceSelector
        +connectController(controller)
        +updateSignal(signalData)
        +activeView()
        +toggleTheme()
        +setTheme(themeName)
    }

    class OscilloscopeView {
        +render(signal)
        +updateSignal(signalData)
        +connectController(controller)
    }

    ioViewBase <|.. ioOscilloscopeViewDark
    ioViewBase <|.. ioOscilloscopeViewLight
    ioViewBase <|.. OscilloscopeView
    ioMainWindow --> ioOscilloscopeViewDark
    ioMainWindow --> ioOscilloscopeViewLight
    ioMainWindow ..> "controller" : setDataSource(...)
    ioMainWindow ..> "controller" : setTheme(...)
    ioMainWindow ..> ioViewBase : forwards updateSignal(...)
```
