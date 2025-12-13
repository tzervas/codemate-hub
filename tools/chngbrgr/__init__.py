"""chngbrgr - Changelog generation package.

This package provides modular changelog generation from tracker documents
with git/PR enrichment, contributor classification, and duplicate suppression.

Modules:
    config: Configuration constants (paths, patterns, mappings)
    models: Data classes for commits and trackers
    trackers: Tracker file parsing and grouping
    git: Git/PR commit enrichment and classification
    render: Snapshot and changelog rendering
"""

from tools.chngbrgr.render import render_changelog

__all__ = ["render_changelog"]
