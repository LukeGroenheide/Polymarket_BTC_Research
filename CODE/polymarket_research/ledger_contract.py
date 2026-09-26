"""Small read-only input contract for the public PM projection example.

Production uses the full private ledger-v2 validator before this projection.
This adapter checks the fields needed by the selected pure research function;
it does not implement ledger publication, readback, or source certification.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping, Iterable

EVENT_LEDGER_SCHEMA_V2_NAME = 'normalized_event_ledger_v2'
CANONICAL_OBSERVATION_ROW_KIND = 'canonical_observation'

@dataclass(frozen=True)
class SourceArtifact:
    role: str
    row_count: int | None

@dataclass(frozen=True)
class EventLedgerSessionManifest:
    manifest_schema: str
    session_id: str
    bucket: str
    market_id: str
    market_slug: str
    window_start_ms: int
    window_end_ms: int
    yes_asset_id: str
    asset_outcomes: tuple[tuple[str, str], ...]
    source_artifacts: tuple[SourceArtifact, ...]

def event_ledger_session_manifest_from_mapping(value: EventLedgerSessionManifest | Mapping[str, Any]) -> EventLedgerSessionManifest:
    if isinstance(value, EventLedgerSessionManifest):
        return value
    if not isinstance(value, Mapping):
        raise ValueError('manifest must be a mapping')
    required = ('manifest_schema','session_id','bucket','market_id','market_slug','window_start_ms','window_end_ms','yes_asset_id','asset_outcomes','source_artifacts')
    if any(k not in value for k in required):
        raise ValueError('manifest missing required field')
    outcomes = tuple((str(x['asset_id']), str(x['outcome'])) for x in value['asset_outcomes'])
    artifacts = tuple(SourceArtifact(str(x['role']), x.get('row_count')) for x in value['source_artifacts'])
    if len(outcomes) != 2 or {v for _, v in outcomes} != {'YES','NO'}:
        raise ValueError('expected explicit YES and NO assets')
    if value['yes_asset_id'] not in {a for a,v in outcomes if v == 'YES'}:
        raise ValueError('YES asset mismatch')
    if len([a for a in artifacts if a.role == 'raw_ndjson']) != 1:
        raise ValueError('raw NDJSON fingerprint required')
    if type(value['window_start_ms']) is not int or type(value['window_end_ms']) is not int:
        raise ValueError('window boundaries must be integer milliseconds')
    return EventLedgerSessionManifest(*(value[k] for k in required[:8]), outcomes, artifacts)

def validate_event_ledger_rows(rows: Iterable[Mapping[str, Any]], *, bucket: str, expected_schema: str) -> None:
    if expected_schema != EVENT_LEDGER_SCHEMA_V2_NAME:
        raise ValueError('expected ledger-v2')
    for i, row in enumerate(rows):
        if row.get('schema') != expected_schema or row.get('bucket') != bucket:
            raise ValueError(f'row {i} schema or bucket mismatch')
        if row.get('row_kind') != CANONICAL_OBSERVATION_ROW_KIND:
            raise ValueError(f'row {i} is not canonical observation')
        if row.get('source_index') != i:
            raise ValueError(f'row {i} source order mismatch')
