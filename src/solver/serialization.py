"""Serialização versionada dos resultados do solver."""

import json


SCHEMA_VERSION = "1"


def summary_dict(summary):
    return {
        "schema_version": SCHEMA_VERSION,
        "status": summary.status.value,
        "unique": summary.unique.value,
        "complete": summary.complete,
        "solutions_emitted": summary.solutions_emitted,
        "classes_seen": summary.classes_seen,
        "backend": summary.backend,
        "backend_version": summary.backend_version,
        "truncated": summary.truncated,
        "details": summary.details,
    }


def summary_json(summary):
    return json.dumps(
        summary_dict(summary), ensure_ascii=False, sort_keys=True
    )
