"""Test-only projection of the explicitly approved additive archive output."""

from copy import deepcopy
from dataclasses import asdict


def prior_candidate(candidate):
    candidate = without_preslot_aliases(candidate)
    if candidate is not None:
        candidate.pop("preslot_archive_double_candidates", None)
        for slot in candidate["slots"]:
            slot.pop("archive_double_candidates", None)
    return candidate


def prior_object_dict(obj):
    result = asdict(obj)
    fields = result["candidate_fields"]
    if "text_slot_run" in fields:
        fields["text_slot_run"] = prior_candidate(fields["text_slot_run"])
    return result


def without_preslot_candidate(candidate):
    """Project to the pre-preslot contract, including later dependent aliases."""
    candidate = without_preslot_aliases(candidate)
    if candidate is not None:
        candidate.pop("preslot_archive_double_candidates", None)
    return candidate


def without_preslot_object(obj):
    result = asdict(obj)
    fields = result["candidate_fields"]
    if "text_slot_run" in fields:
        fields["text_slot_run"] = without_preslot_candidate(fields["text_slot_run"])
    return result


def without_preslot_aliases(candidate):
    """Remove only the approved alias map; all eight canonical fields remain."""
    candidate = deepcopy(candidate)
    if candidate is not None:
        candidate.pop("preslot_archive_double_aliases", None)
    return candidate


def without_preslot_alias_object(obj):
    result = asdict(obj)
    fields = result["candidate_fields"]
    if "text_slot_run" in fields:
        fields["text_slot_run"] = without_preslot_aliases(fields["text_slot_run"])
    return result
