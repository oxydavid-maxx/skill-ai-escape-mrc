"""JSON schemas for structured phase outputs.

Passed to call_claude(json_schema=...) → Claude CLI uses --json-schema
for constrained decoding. Output is guaranteed schema-valid.

Anthropic API requires top-level type to be 'object' — array-of-strings
results are wrapped in a single-key object for that reason.
"""

KEYWORD_EXTRACTION = {
    "type": "object",
    "properties": {
        "keywords": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 5,
        }
    },
    "required": ["keywords"],
}

META_CATEGORIZATION = {
    "type": "object",
    "properties": {
        "categories": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 3,
        },
        "domains": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 3,
        },
    },
    "required": ["categories", "domains"],
}

SEARCH_REFLECTION = {
    "type": "object",
    "properties": {
        "reframing": {"type": "string"},
        "higher_level_question": {"type": "string"},
        "wave2_queries": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 2,
            "maxItems": 4,
        },
    },
    "required": ["reframing", "higher_level_question", "wave2_queries"],
}

WIKI_SLUG_SELECTION = {
    "type": "object",
    "properties": {
        "slugs": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 5,
        }
    },
    "required": ["slugs"],
}

_IS_ISNT_DIM = {
    "type": "object",
    "properties": {
        "is": {"type": "string"},
        "is_not": {"type": "string"},
        "distinction": {"type": "string"},
    },
    "required": ["is", "is_not", "distinction"],
}

IS_ISNT_EXTRACTION = {
    "type": "object",
    "properties": {
        "what": _IS_ISNT_DIM,
        "where": _IS_ISNT_DIM,
        "when": _IS_ISNT_DIM,
        "extent": _IS_ISNT_DIM,
    },
    "required": ["what", "where", "when", "extent"],
}

WHY_ANALYSIS = {
    "type": "object",
    "properties": {
        "quadrant": {"type": "string"},
        "whys": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "n": {"type": "integer"},
                    "why": {"type": "string"},
                    "new_insight": {"type": "string"},
                },
                "required": ["n", "why"],
            },
            "minItems": 10,
        },
        "root": {"type": "string"},
    },
    "required": ["quadrant", "whys", "root"],
}

RC_AUDIT = {
    "type": "object",
    "properties": {
        "round": {"type": "integer"},
        "weaknesses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "quadrant": {"type": "string"},
                    "why_step_n": {"type": ["integer", "null"]},
                    "classification": {
                        "type": "string",
                        "enum": ["ADDRESSABLE", "RESIDUAL"],
                    },
                    "issue": {"type": "string"},
                    "suggested_fix": {"type": "string"},
                    "evidence": {"type": "string"},
                },
                "required": ["quadrant", "classification", "issue"],
            },
        },
        "verdict": {
            "type": "string",
            "enum": ["CONTINUE", "EXHAUSTED", "REWORK"],
        },
    },
    "required": ["round", "weaknesses", "verdict"],
}

CORRECTIVE_ACTION = {
    "type": "object",
    "properties": {
        "quadrant": {"type": "string"},
        "action": {"type": "string"},
        "rationale": {"type": "string"},
        "owner": {"type": "string"},
        "target_date": {"type": "string"},
        "evidence_of_completion": {"type": "string"},
    },
    "required": ["quadrant", "action", "rationale"],
}

PREVENTION_ACTION = {
    "type": "object",
    "properties": {
        "quadrant": {"type": "string"},
        "action": {"type": "string"},
        "gate_test": {
            "type": "object",
            "properties": {
                "scope": {"type": "string", "enum": ["PASS", "FAIL"]},
                "scope_evidence": {"type": "string"},
                "persistence": {"type": "string", "enum": ["PASS", "FAIL"]},
                "persistence_evidence": {"type": "string"},
                "measurability": {"type": "string", "enum": ["PASS", "FAIL"]},
                "measurability_evidence": {"type": "string"},
            },
            "required": ["scope", "persistence", "measurability"],
        },
        "hierarchy_level": {"type": "integer", "minimum": 1, "maximum": 5},
        "failure_mode_of_prevention": {"type": "string"},
        "deployment_scope": {"type": "string", "enum": ["PROJECT", "GLOBAL"]},
        "scope_justification": {"type": "string"},
    },
    "required": ["quadrant", "action", "gate_test", "hierarchy_level"],
}

PREVENTION_AUDIT = {
    "type": "object",
    "properties": {
        "round": {"type": "integer"},
        "weaknesses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "quadrant": {"type": "string"},
                    "classification": {
                        "type": "string",
                        "enum": ["ADDRESSABLE", "RESIDUAL"],
                    },
                    "issue": {"type": "string"},
                    "suggested_fix": {"type": "string"},
                    "evidence": {"type": "string"},
                },
                "required": ["quadrant", "classification", "issue"],
            },
        },
        "verdict": {
            "type": "string",
            "enum": ["CONTINUE", "EXHAUSTED", "REWORK"],
        },
    },
    "required": ["round", "weaknesses", "verdict"],
}

VERIFICATION_PLAN = {
    "type": "object",
    "properties": {
        "quadrants": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "quadrant": {"type": "string"},
                    "action_type": {
                        "type": "string",
                        "enum": ["corrective", "prevention"],
                    },
                    "metric": {"type": "string"},
                    "data_source": {"type": "string"},
                    "target": {"type": "string"},
                    "baseline": {"type": "string"},
                    "measurement_schedule": {"type": "string"},
                    "failure_response": {"type": "string"},
                },
                "required": ["quadrant", "action_type", "metric", "target"],
            },
            "minItems": 4,
            "maxItems": 4,
        },
        "overall_timeframe": {"type": "string"},
        "phase_8_trigger": {"type": "string"},
    },
    "required": ["quadrants", "overall_timeframe"],
}
