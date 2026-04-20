from __future__ import annotations

from .io_sample_mapping_filter_base import ioSampleMappingFilterBase


class ioScaleFilter(ioSampleMappingFilterBase):
    FILTER_NAME = "ioScaleFilter"

    def __init__(self, scaleFactor: float):
        self.scaleFactor = scaleFactor

    def _transform_sample(self, sample: float) -> float:
        return sample * self.scaleFactor


scpScale = ioScaleFilter
