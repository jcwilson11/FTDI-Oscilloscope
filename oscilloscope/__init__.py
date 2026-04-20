"""Demo-ready MVC + pipe-and-filter oscilloscope architecture."""

from ._qt_compat import PLOT_AVAILABLE, PLOT_IMPORT_ERROR, QT_AVAILABLE, QT_IMPORT_ERROR
from .controller import OscilloscopeController, ioOscilloscopeController
from .filters import (
    FilterPipeline,
    ISignalFilter,
    ioFilterPipeline,
    ioOffsetFilter,
    ioScaleFilter,
    ioSignalFilter,
    scpOffset,
    scpScale,
)
from .io_compact_oscilloscope_view import ioCompactOscilloscopeView
from .io_control_state import ioControlState
from .io_detailed_oscilloscope_view import ioDetailedOscilloscopeView
from .io_file_waveform_source import FileWaveformSource, ioFileWaveformSource
from .io_ftdi_waveform_source import ioFtdiWaveformSource
from .io_generated_waveform_source import GeneratedWaveformSource, ioGeneratedWaveformSource
from .io_landscape_theme import ioLandscapeTheme
from .io_live_file_tail_byte_stream import ioLiveFileTailByteStream
from .io_live_oscilloscope_session import ioLiveOscilloscopeSession
from .io_live_sample_history import ioLiveSampleHistory
from .io_null_writable_byte_stream import ioNullWritableByteStream
from .io_oscilloscope_model import OscilloscopeModel, ioOscilloscopeModel
from .io_oscilloscope_view import ioOscilloscopeView
from .io_oscilloscope_window import OscilloscopeWindow, ioOscilloscopeWindow
from .io_portrait_theme import ioPortraitTheme
from .io_qt_scope_window import ioQtScopeWindow
from .io_render_state import ioRenderState
from .io_sample_mapping_filter_base import SampleMappingFilterBase, ioSampleMappingFilterBase
from .io_scope_settings_store import ioScopeSettingsStore
from .io_signal_source import SignalSource, ioSignalSource
from .io_static_theme_base import StaticThemeBase, ioStaticThemeBase
from .io_tapped_readable_byte_stream import ioTappedReadableByteStream
from .io_tk_oscilloscope_window import ioTkOscilloscopeWindow
from .io_view_theme import ioViewTheme
from .io_viewport_state import ioViewportState
from .io_waveform_generator import ioWaveformGenerator
from .view import OscilloscopeView

__all__ = [
    "FileWaveformSource",
    "FilterPipeline",
    "GeneratedWaveformSource",
    "ISignalFilter",
    "OscilloscopeController",
    "OscilloscopeModel",
    "OscilloscopeWindow",
    "OscilloscopeView",
    "SignalSource",
    "SampleMappingFilterBase",
    "StaticThemeBase",
    "QT_AVAILABLE",
    "QT_IMPORT_ERROR",
    "PLOT_AVAILABLE",
    "PLOT_IMPORT_ERROR",
    "ioControlState",
    "ioCompactOscilloscopeView",
    "ioDetailedOscilloscopeView",
    "ioFileWaveformSource",
    "ioFilterPipeline",
    "ioFtdiWaveformSource",
    "ioGeneratedWaveformSource",
    "ioLandscapeTheme",
    "ioLiveFileTailByteStream",
    "ioLiveOscilloscopeSession",
    "ioLiveSampleHistory",
    "ioNullWritableByteStream",
    "ioOffsetFilter",
    "ioOscilloscopeController",
    "ioOscilloscopeModel",
    "ioOscilloscopeView",
    "ioOscilloscopeWindow",
    "ioPortraitTheme",
    "ioQtScopeWindow",
    "ioRenderState",
    "ioSampleMappingFilterBase",
    "ioScopeSettingsStore",
    "ioScaleFilter",
    "ioSignalFilter",
    "ioSignalSource",
    "ioStaticThemeBase",
    "ioTappedReadableByteStream",
    "ioTkOscilloscopeWindow",
    "ioViewTheme",
    "ioViewportState",
    "ioWaveformGenerator",
    "scpOffset",
    "scpScale",
]
