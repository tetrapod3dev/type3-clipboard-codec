"""Test-only projection of the explicitly approved additive archive output."""

from copy import deepcopy
from dataclasses import asdict


def prior_candidate(candidate):
    candidate = deepcopy(candidate)
    if candidate is not None:
        for slot in candidate["slots"]:
            slot.pop("archive_double_candidates", None)
    return candidate


def prior_object_dict(obj):
    result = asdict(obj)
    fields = result["candidate_fields"]
    if "text_slot_run" in fields:
        fields["text_slot_run"] = prior_candidate(fields["text_slot_run"])
    return result
