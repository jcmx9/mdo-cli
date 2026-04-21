from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from mdo.core.models import ProfileConfig
from mdo.core.profile import delete_profile, list_profiles, load_profile, save_profile


@pytest.fixture
def profiles_path(tmp_path: Path) -> Path:
    d = tmp_path / ".mdo" / "profiles"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def _mock_profiles_dir(profiles_path: Path):  # type: ignore[no-untyped-def]
    with patch("mdo.core.profile.profiles_dir", return_value=profiles_path):
        yield


@pytest.fixture
def sample_profile() -> ProfileConfig:
    return ProfileConfig(
        name="Max Mustermann",
        street="Musterstrasse 1",
        zip="12345",
        city="Musterstadt",
    )


@pytest.mark.usefixtures("_mock_profiles_dir")
class TestSaveProfile:
    def test_save_default(self, profiles_path: Path, sample_profile: ProfileConfig) -> None:
        result = save_profile(sample_profile)
        assert result == profiles_path / "default" / "profile.yaml"
        assert result.exists()
        data = yaml.safe_load(result.read_text())
        assert data["name"] == "Max Mustermann"

    def test_save_named(self, profiles_path: Path, sample_profile: ProfileConfig) -> None:
        result = save_profile(sample_profile, name="work")
        assert result == profiles_path / "work" / "profile.yaml"
        assert result.exists()


@pytest.mark.usefixtures("_mock_profiles_dir")
class TestLoadProfile:
    def test_load_existing(self, profiles_path: Path, sample_profile: ProfileConfig) -> None:
        save_profile(sample_profile, name="test")
        loaded = load_profile("test")
        assert loaded.name == "Max Mustermann"
        assert loaded.street == "Musterstrasse 1"

    def test_load_nonexistent_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_profile("nonexistent")

    def test_load_default(self, profiles_path: Path, sample_profile: ProfileConfig) -> None:
        save_profile(sample_profile)
        loaded = load_profile()
        assert loaded.name == "Max Mustermann"


@pytest.mark.usefixtures("_mock_profiles_dir")
class TestListProfiles:
    def test_list_empty(self) -> None:
        assert list_profiles() == []

    def test_list_multiple(self, profiles_path: Path, sample_profile: ProfileConfig) -> None:
        save_profile(sample_profile, name="default")
        save_profile(sample_profile, name="work")
        names = list_profiles()
        assert sorted(names) == ["default", "work"]


@pytest.mark.usefixtures("_mock_profiles_dir")
class TestDeleteProfile:
    def test_delete_existing(self, profiles_path: Path, sample_profile: ProfileConfig) -> None:
        save_profile(sample_profile, name="default")
        save_profile(sample_profile, name="temp")
        delete_profile("temp")
        assert not (profiles_path / "temp").exists()

    def test_delete_nonexistent_raises(
        self, profiles_path: Path, sample_profile: ProfileConfig
    ) -> None:
        save_profile(sample_profile, name="default")
        save_profile(sample_profile, name="other")
        with pytest.raises(FileNotFoundError):
            delete_profile("nonexistent")

    def test_delete_last_profile_raises(
        self, profiles_path: Path, sample_profile: ProfileConfig
    ) -> None:
        save_profile(sample_profile)
        with pytest.raises(ValueError, match="last"):
            delete_profile("default")
