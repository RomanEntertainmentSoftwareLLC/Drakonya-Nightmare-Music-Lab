from app.tools.drakonya import main


def test_drakonya_cli_help_exists(monkeypatch):
    monkeypatch.setattr("sys.argv", ["drakonya", "--help"])

    try:
        main()
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("Expected SystemExit")


def test_drakonya_sidecar_command_invokes_uvicorn(monkeypatch):
    called = {}

    def fake_run(app, host, port, reload):
        called["app"] = app
        called["host"] = host
        called["port"] = port
        called["reload"] = reload

    monkeypatch.setattr("app.tools.drakonya.uvicorn.run", fake_run)
    monkeypatch.setattr(
        "sys.argv",
        ["drakonya", "sidecar", "--host", "127.0.0.1", "--port", "8766"],
    )

    main()

    assert called["app"] == "sidecar.suno_sidecar:app"
    assert called["host"] == "127.0.0.1"
    assert called["port"] == 8766
    assert called["reload"] is False
