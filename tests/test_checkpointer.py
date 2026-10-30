from types import SimpleNamespace

from graph.checkpointer import _configured_checkpoint_path


def test_checkpoint_path_uses_configured_setting(monkeypatch, tmp_path):
    configured_path = str(tmp_path / "custom-checkpoints.sqlite")
    monkeypatch.delenv("SUPPORT_CHECKPOINT_DB_PATH", raising=False)
    monkeypatch.setattr(
        "graph.checkpointer.get_settings",
        lambda: SimpleNamespace(checkpoint_path=configured_path),
    )

    assert _configured_checkpoint_path() == configured_path


def test_legacy_checkpoint_environment_variable_takes_precedence(
    monkeypatch, tmp_path
):
    configured_path = str(tmp_path / "configured.sqlite")
    legacy_path = str(tmp_path / "legacy.sqlite")
    monkeypatch.setenv("SUPPORT_CHECKPOINT_DB_PATH", legacy_path)
    monkeypatch.setattr(
        "graph.checkpointer.get_settings",
        lambda: SimpleNamespace(checkpoint_path=configured_path),
    )

    assert _configured_checkpoint_path() == legacy_path
