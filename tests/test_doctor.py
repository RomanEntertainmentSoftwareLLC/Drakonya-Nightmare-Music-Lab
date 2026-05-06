from app.tools.doctor import doctor


def test_doctor_reports_missing_sidecar(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DRAKONYA_ROOT", str(tmp_path))
    (tmp_path / "app").mkdir()
    (tmp_path / "sidecar").mkdir()
    (tmp_path / "sidecar" / "suno_sidecar.py").write_text("# sidecar")
    (tmp_path / "data" / "inbox" / "suno_downloads").mkdir(parents=True)

    result = doctor("http://127.0.0.1:1")
    output = capsys.readouterr().out

    assert result == 1
    assert "Drakonya Doctor" in output
    assert "sidecar not reachable" in output
    assert "python3 -m app.tools.drakonya sidecar" in output
