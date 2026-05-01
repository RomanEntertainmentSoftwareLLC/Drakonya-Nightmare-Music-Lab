from app.core.paths import (
    project_root,
    data_dir,
    tracks_dir,
    covers_dir,
    videos_dir,
    releases_dir,
    analytics_dir,
    slop_bin_dir,
    agents_dir,
    docs_dir,
)


def test_project_paths_exist():
    assert project_root().exists()
    assert data_dir().exists()
    assert tracks_dir().exists()
    assert covers_dir().exists()
    assert videos_dir().exists()
    assert releases_dir().exists()
    assert analytics_dir().exists()
    assert slop_bin_dir().exists()
    assert agents_dir().exists()
    assert docs_dir().exists()
