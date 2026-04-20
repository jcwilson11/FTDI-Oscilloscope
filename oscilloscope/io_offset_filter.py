from __future__ import annotations

from .io_sample_mapping_filter_base import ioSampleMappingFilterBase


class ioOffsetFilter(ioSampleMappingFilterBase):
    FILTER_NAME = "ioOffsetFilter"

    def __init__(self, offsetValue: float):
        self.offsetValue = offsetValue

    def _transform_sample(self, sample: float) -> float:
        return sample + self.offsetValue


scpOffset = ioOffsetFilter
