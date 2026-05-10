from .cparagraphe_parser import (
    attach_text_anchor_candidates,
    attach_text_runs_to_chains,
    extract_candidate_text_records,
    extract_font_candidates,
    extract_font_name,
    extract_text_runs,
    read_paragraphe_slot_record_runs,
    read_slot_record_runs_from_blob,
    records_to_text_run,
)

__all__ = [
    "attach_text_anchor_candidates",
    "attach_text_runs_to_chains",
    "extract_candidate_text_records",
    "extract_font_candidates",
    "extract_font_name",
    "extract_text_runs",
    "read_paragraphe_slot_record_runs",
    "read_slot_record_runs_from_blob",
    "records_to_text_run",
]
