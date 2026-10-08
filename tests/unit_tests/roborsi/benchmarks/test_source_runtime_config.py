# Copyright 2026 The HEART Authors.
# Licensed under the Apache License, Version 2.0 (the "License");

"""Tests for the three-LIBERO source-runtime preflight."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.libero_three.prepare_agent_assets import prepare as prepare_agent_assets
from scripts.libero_three.prepare_context import _destination_name


def test_pro_context_export_uses_a_public_stable_alias() -> None:
    package = SimpleNamespace(package_id="private-source-name")

    assert (
        _destination_name("libero_pro", "libero_spatial_swap-t07-i03", package)
        == "libero-pro-context-spatial-t07"
    )
    assert _destination_name("libero_ultra_long", "t00-i01", package) == (
        "private-source-name"
    )


def test_agent_asset_lock_records_content_snapshots() -> None:
    repository = Path(__file__).resolve().parents[4]
    lock = json.loads(
        (repository / "configs/libero_three/assets.lock.json").read_text()
    )

    for name in (
        "libero_long_plus_plus_icl",
        "libero_ultra_long_icl",
        "libero_pro_icl",
    ):
        assert len(lock["assets"][name]["snapshot_sha256"]) == 64


def test_agent_asset_staging_requires_all_three_roots(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="expected ICL roots"):
        prepare_agent_assets(
            {},
            tmp_path / "tokenizer.json",
            tmp_path / "output",
            repository=tmp_path,
        )
