import pytest

@pytest.fixture
def sample_fixture():
    return "Hello, World!"

def test_sample_fixture(sample_fixture):
    assert sample_fixture == "Hello, World!"