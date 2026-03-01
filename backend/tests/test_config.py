"""Tests for config.py module loading logic."""

import sys
import os
import types
import importlib
import tempfile
import pytest
from unittest.mock import patch, MagicMock


# Backend root for path manipulation
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, BACKEND_DIR)


def _reload_config(env_vars=None, secrets_content=None):
    """Reload config.py with controlled environment.

    Temporarily removes the config stub from sys.modules, sets up env vars
    and optionally a secrets file, then imports config fresh.
    """
    # Ensure mistralai is stubbed so `Mistral(api_key=...)` doesn't fail
    _mistralai = types.ModuleType("mistralai")
    _mistralai.Mistral = MagicMock()
    sys.modules["mistralai"] = _mistralai

    # Stub dotenv so load_dotenv() is a no-op
    _dotenv = types.ModuleType("dotenv")
    _dotenv.load_dotenv = lambda: None
    sys.modules["dotenv"] = _dotenv

    # Remove cached config module so importlib.reload actually re-executes it
    if "config" in sys.modules:
        del sys.modules["config"]

    env = env_vars or {}

    with patch.dict(os.environ, env, clear=False):
        # Remove MISTRAL_API_KEY from env if not explicitly provided
        if "MISTRAL_API_KEY" not in env and "MISTRAL_API_KEY" in os.environ:
            del os.environ["MISTRAL_API_KEY"]

        if secrets_content is not None:
            # Create a temp directory structure with .secrets/mistral_api_key
            with tempfile.TemporaryDirectory() as tmpdir:
                secrets_dir = os.path.join(tmpdir, ".secrets")
                os.makedirs(secrets_dir)
                secrets_path = os.path.join(secrets_dir, "mistral_api_key")
                with open(secrets_path, "w") as f:
                    f.write(secrets_content)
                # Patch the project_root calculation to point to our temp dir
                with patch("os.path.dirname") as mock_dirname:
                    # config.py does: dirname(dirname(abspath(__file__)))
                    # We need the outer dirname call to return tmpdir
                    def dirname_side_effect(path):
                        # Use real dirname for all calls
                        return os.path.dirname.__wrapped__(path) if hasattr(os.path.dirname, '__wrapped__') else _real_dirname(path)

                    # Simpler approach: patch at the point where secrets_path is constructed
                    import config
                    return config
        else:
            import config
            return config


# Save real os.path.dirname before any patching
_real_dirname = os.path.dirname


class TestConfigLoadsFromEnvVar:
    def test_config_loads_from_env_var(self):
        """When MISTRAL_API_KEY is in env, config picks it up."""
        # Stub out dependencies
        _mistralai = types.ModuleType("mistralai")
        _mistralai.Mistral = MagicMock()
        sys.modules["mistralai"] = _mistralai

        _dotenv = types.ModuleType("dotenv")
        _dotenv.load_dotenv = lambda: None
        sys.modules["dotenv"] = _dotenv

        saved = sys.modules.pop("config", None)
        try:
            with patch.dict(os.environ, {"MISTRAL_API_KEY": "test-env-key"}, clear=False):
                import config
                importlib.reload(config)
                assert config.MISTRAL_API_KEY == "test-env-key"
                assert config.AUDIO_MODEL == "voxtral-mini-latest"
                assert config.TEXT_MODEL == "mistral-large-latest"
        finally:
            # Restore the stub so other tests aren't affected
            sys.modules.pop("config", None)
            if saved is not None:
                sys.modules["config"] = saved


class TestConfigLoadsFromSecretsFile:
    def test_config_loads_from_secrets_file(self):
        """When env var is unset, config reads from .secrets/mistral_api_key."""
        _mistralai = types.ModuleType("mistralai")
        _mistralai.Mistral = MagicMock()
        sys.modules["mistralai"] = _mistralai

        _dotenv = types.ModuleType("dotenv")
        _dotenv.load_dotenv = lambda: None
        sys.modules["dotenv"] = _dotenv

        saved = sys.modules.pop("config", None)
        try:
            # Create a temp secrets file
            with tempfile.TemporaryDirectory() as tmpdir:
                secrets_dir = os.path.join(tmpdir, ".secrets")
                os.makedirs(secrets_dir)
                with open(os.path.join(secrets_dir, "mistral_api_key"), "w") as f:
                    f.write("test-secret-file-key\n")

                # Remove env var if present
                env = os.environ.copy()
                env.pop("MISTRAL_API_KEY", None)

                with patch.dict(os.environ, env, clear=True):
                    # Patch the project_root to point at tmpdir
                    # config.py line 10: project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    # We need dirname(dirname(abspath(config.__file__))) == tmpdir
                    config_path = os.path.join(BACKEND_DIR, "config.py")
                    real_abspath = os.path.abspath

                    def fake_abspath(path):
                        if path == "__file__" or (isinstance(path, str) and path.endswith("config.py")):
                            # Return a path such that dirname(dirname(x)) == tmpdir
                            return os.path.join(tmpdir, "backend", "config.py")
                        return real_abspath(path)

                    with patch("os.path.abspath", side_effect=fake_abspath):
                        import config
                        importlib.reload(config)
                        assert config.MISTRAL_API_KEY == "test-secret-file-key"
        finally:
            sys.modules.pop("config", None)
            if saved is not None:
                sys.modules["config"] = saved


class TestConfigRaisesWhenNoKey:
    def test_config_raises_when_no_key(self):
        """When no env var and no secrets file, config raises RuntimeError."""
        _mistralai = types.ModuleType("mistralai")
        _mistralai.Mistral = MagicMock()
        sys.modules["mistralai"] = _mistralai

        _dotenv = types.ModuleType("dotenv")
        _dotenv.load_dotenv = lambda: None
        sys.modules["dotenv"] = _dotenv

        saved = sys.modules.pop("config", None)
        try:
            env = os.environ.copy()
            env.pop("MISTRAL_API_KEY", None)

            with patch.dict(os.environ, env, clear=True):
                # Point project root at a temp dir with no secrets file
                with tempfile.TemporaryDirectory() as tmpdir:
                    real_abspath = os.path.abspath

                    def fake_abspath(path):
                        if isinstance(path, str) and path.endswith("config.py"):
                            return os.path.join(tmpdir, "backend", "config.py")
                        return real_abspath(path)

                    with patch("os.path.abspath", side_effect=fake_abspath):
                        with pytest.raises(RuntimeError, match="MISTRAL_API_KEY not set"):
                            import config
                            importlib.reload(config)
        finally:
            sys.modules.pop("config", None)
            if saved is not None:
                sys.modules["config"] = saved
