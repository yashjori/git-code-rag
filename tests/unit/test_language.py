from pathlib import Path

from app.ingestion.language import detect_language


class TestDetectLanguage:
    def test_python(self):
        assert detect_language(Path("app/auth/service.py")) == "python"

    def test_typescript(self):
        assert detect_language(Path("src/index.tsx")) == "typescript"

    def test_dockerfile_by_filename(self):
        assert detect_language(Path("Dockerfile")) == "dockerfile"

    def test_package_json_by_filename(self):
        assert detect_language(Path("package.json")) == "json"

    def test_unknown_extension_falls_back_to_text(self):
        assert detect_language(Path("data.unknownext")) == "text"

    def test_sql(self):
        assert detect_language(Path("migrations/001_init.sql")) == "sql"
