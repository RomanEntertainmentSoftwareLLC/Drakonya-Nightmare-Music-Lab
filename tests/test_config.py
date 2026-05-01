from app.core.config import load_config, assert_llm_allowed


def test_config_loads_disabled_by_default():
    config = load_config()

    assert config.root.exists()
    assert config.openai_enabled is False
    assert config.agent_automation_enabled is False
    assert config.max_run_llm_usd <= 0.10


def test_llm_guard_blocks_by_default():
    try:
        assert_llm_allowed()
    except RuntimeError as exc:
        assert "disabled" in str(exc).lower()
    else:
        raise AssertionError("LLM guard should block by default")
