# ioScope Quality Attribute Tactics

This note supports the rubric item asking for class or structural diagrams that show tactics for availability, performance, usability, security, safety, and energy efficiency. The overview diagram is [docs/plantuml/io_scope_quality_attribute_tactics.puml](../plantuml/io_scope_quality_attribute_tactics.puml), and each quality attribute now has its own focused companion file.

The split diagrams are intentionally honest about scope:
- `<<implemented>>` classes already exist in the current codebase.
- `<<proposed>>` classes are architectural extensions added to show how the design would satisfy the broader quality-attribute rubric, especially for the networked lab scenario described in the write-up.

## Diagram Set

- [Availability](../plantuml/io_scope_quality_attribute_availability.puml)
- [Performance](../plantuml/io_scope_quality_attribute_performance.puml)
- [Usability](../plantuml/io_scope_quality_attribute_usability.puml)
- [Security](../plantuml/io_scope_quality_attribute_security.puml)
- [Safety](../plantuml/io_scope_quality_attribute_safety.puml)
- [Energy Efficiency](../plantuml/io_scope_quality_attribute_energy_efficiency.puml)

## Attribute Summary

| Quality attribute | Tactic shown in the diagram | Main classes | Brief rationale |
| --- | --- | --- | --- |
| Availability | Health monitoring, supervised restart, restore last safe configuration | `ioHealthMonitor`, `ioSessionSupervisor`, `ioRecoveryManager`, `ioScopeSettingsStore` | If FTDI access or a remote stream fails temporarily, the oscilloscope should recover quickly without requiring a full UI restart. |
| Performance | Concurrency, bounded buffering, explicit scheduling, acquisition-first prioritization | `ioPipelineController`, `ioDataBuffer`, `ioUsbReadController`, `ioUsbWriteController`, `ioInputScheduler`, `ioOutputScheduler` | Time-sensitive capture should stay responsive even when rendering, logging, or remote sharing creates extra load. |
| Usability | Task presets, saved settings, inline validation feedback | `ioQtScopeWindow`, `ioCapturePresetCatalog`, `ioValidationFeedbackService`, `ioScopeSettingsStore` | Common tasks should take only a few actions and give fast visible feedback, matching the response measures from the usability scenarios. |
| Security | Authentication, authorization, auditing, mediated remote access | `ioRemoteAccessGateway`, `ioAuthenticator`, `ioAuthorizationPolicy`, `ioAuditLog` | Remote monitoring is useful in a networked lab, but unauthorized users should not be able to change settings or interfere with measurements. |
| Safety | Safe defaults, range validation, remote interlock, stop or clamp on unsafe operation | `ioSafetyGuard`, `ioSafeRangeProfile`, `ioRemoteInterlock` | Incorrect limits or remote commands could invalidate results or damage connected circuits, so risky changes should be blocked or confirmed. |
| Energy efficiency | Idle detection, sleep control, display dimming, fast wake-up | `ioEnergyManager`, `ioIdleMonitor`, `ioSleepController`, `ioWakeController`, `ioDisplayController`, `ioAcquisitionPowerController` | The oscilloscope may remain powered on throughout the day, so idle periods should consume less power while preserving quick readiness. |

## Using Your Write-Up In The Presentation

These points map directly to the text you already wrote:

- Usability: your response measures already give concrete targets such as "five user actions or fewer" and "waveform begins within 100 ms." The usability diagram turns those goals into structural tactics like presets, saved state, and inline validation.
- Security: your networking section says remote labs should be able to share data without allowing unauthorized reconfiguration. The security diagram expresses that through a gateway, authentication, authorization, and audit logging.
- Safety: your trade-off section says the system should use safe defaults, validate configuration changes, warn users about unsafe limits, and restrict remote users to read-only unless they have higher privileges. Those ideas are represented by `ioSafetyGuard`, `ioSafeRangeProfile`, and `ioRemoteInterlock`.
- Performance: your write-up says acquisition should be prioritized over secondary features such as remote updates or nonessential rendering. The performance diagram shows that by keeping the existing worker threads and bounded buffer at the center of the performance path.
- Energy efficiency: the `ioEnergyManager`, `ioIdleMonitor`, `ioSleepController`, and `ioWakeController` package comes directly from the CRC-based energy design you already prepared.
- Availability: this was less explicit in the write-up, so the availability diagram adds a supervised recovery path to complete the rubric coverage. It fits naturally with the existing `ioRecoveryManager` and saved settings store.

## Short Presenter Script

If you want a concise way to explain the artifact in class:

1. I split the original oversized quality-attribute diagram into six smaller structural diagrams so each attribute can be explained clearly.
2. Each diagram mixes real implemented oscilloscope classes with a few proposed tactic classes where the rubric asks for architectural intent beyond the current code.
3. The performance diagram stays closest to the implemented code, while security, safety, availability, and energy efficiency show the clearest design extensions for a networked laboratory deployment.
4. Each file includes a short rationale note so the diagram shows not only structure, but also why that structure supports the quality attribute.
