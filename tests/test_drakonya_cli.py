from app.tools.drakonya import main


def test_drakonya_cli_help_exists(monkeypatch):
    monkeypatch.setattr("sys.argv", ["drakonya", "--help"])

    try:
        main()
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("Expected SystemExit")
