from dataclasses import dataclass

from app.intelligence.evidence import CorrelatedEvidence
from app.intelligence.timeline import TimelineEvent
from app.simulation.models import Incident


@dataclass
class IncidentContext:
    incident: Incident
    timeline: list[TimelineEvent]
    evidence: CorrelatedEvidence


def build_incident_context(
    incident: Incident,
    timeline: list[TimelineEvent],
    evidence: CorrelatedEvidence,
) -> IncidentContext:
    return IncidentContext(
        incident=incident,
        timeline=timeline,
        evidence=evidence,
    )
