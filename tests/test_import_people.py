from pathlib import Path
import importlib.util
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/import_people.py"
SPEC = importlib.util.spec_from_file_location("import_people", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

def test_accepts_email(tmp_path):
    f = tmp_path / "people_demo_seed.csv"
    f.write_text("person_id,full_name,email\nP-1,Demo Person,Person@Example.test\n", encoding="utf-8")
    assert module.load_rows(f)[0]["email"] == "person@example.test"

@pytest.mark.parametrize("email", ["not-an-email", "person@", "@example.com", "a b@example.com"])
def test_rejects_invalid_email(tmp_path, email):
    f = tmp_path / "people_demo_seed.csv"
    f.write_text(f"person_id,full_name,email\nP-1,Demo Person,{email}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid email format"):
        module.load_rows(f)
