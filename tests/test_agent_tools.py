from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import Settings
from app.services.agent_tools import AgentTools


class AgentToolsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.workspace = Path(cls.temp_dir.name).resolve()
        cls.settings = Settings(CODE_WORKSPACE_ROOT=str(cls.workspace))
        cls.tools = AgentTools(cls.settings)
        # Create a realistic workspace tree
        (cls.workspace / "src").mkdir()
        (cls.workspace / "src" / "app.py").write_text(
            "def hello():\n    print('hello world')\n", encoding="utf-8"
        )
        (cls.workspace / "src" / "utils.py").write_text(
            "def add(a, b):\n    return a + b\n\ndef multiply(a, b):\n    return a * b\n",
            encoding="utf-8",
        )
        (cls.workspace / "README.md").write_text("# Test Project\n", encoding="utf-8")
        (cls.workspace / ".env").write_text("SECRET=abc123\n", encoding="utf-8")
        (cls.workspace / ".env.example").write_text("SECRET=replace_me\n", encoding="utf-8")
        (cls.workspace / "secret.key").write_text("private key content\n", encoding="utf-8")
        (cls.workspace / "cert.pem").write_text("cert content\n", encoding="utf-8")
        (cls.workspace / "data.db").write_text("sqlite data\n", encoding="utf-8")
        # Ignored directory with files
        (cls.workspace / ".git").mkdir()
        (cls.workspace / ".git" / "config").write_text("[core]\n", encoding="utf-8")
        (cls.workspace / "node_modules").mkdir()
        (cls.workspace / "node_modules" / "pkg").mkdir()
        (cls.workspace / "node_modules" / "pkg" / "index.js").write_text(
            "module.exports = {};\n", encoding="utf-8"
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir.cleanup()

    # ── Path safety ──────────────────────────────────
    def test_resolve_safe_rejects_traversal(self) -> None:
        with self.assertRaises(PermissionError):
            self.tools._resolve_safe("../etc/passwd")

    def test_resolve_safe_rejects_absolute_path_outside(self) -> None:
        with self.assertRaises(PermissionError):
            self.tools._resolve_safe("C:/Windows/System32")

    def test_resolve_safe_allows_normal_path(self) -> None:
        resolved = self.tools._resolve_safe("src/app.py")
        self.assertEqual(resolved, (self.workspace / "src" / "app.py").resolve())

    def test_resolve_safe_allows_root_dot(self) -> None:
        resolved = self.tools._resolve_safe(".")
        self.assertEqual(resolved, self.workspace)

    # ── list_directory ───────────────────────────────
    def test_list_root(self) -> None:
        result = json.loads(self.tools.list_directory("."))
        self.assertIn("entries", result)
        names = [e["name"] for e in result["entries"]]
        self.assertIn("README.md", names)
        self.assertIn("src", names)
        self.assertIn(".env.example", names)
        self.assertNotIn(".git", names)
        self.assertNotIn("node_modules", names)

    def test_list_subdir(self) -> None:
        result = json.loads(self.tools.list_directory("src"))
        names = [e["name"] for e in result["entries"]]
        self.assertIn("app.py", names)
        self.assertIn("utils.py", names)

    def test_list_ignored_dir(self) -> None:
        result = json.loads(self.tools.list_directory(".git"))
        self.assertIn("entries", result)
        self.assertEqual(len(result["entries"]), 0)

    def test_list_traversal_rejected(self) -> None:
        result = json.loads(self.tools.list_directory("../"))
        self.assertIn("error", result)
        self.assertIn("outside workspace", result["error"])

    # ── read_file ────────────────────────────────────
    def test_read_file_normal(self) -> None:
        result = json.loads(self.tools.read_file("src/app.py"))
        self.assertIn("content", result)
        self.assertIn("def hello()", result["content"])

    def test_read_file_with_offset_and_limit(self) -> None:
        result = json.loads(
            self.tools.read_file("src/utils.py", offset=0, limit=25)
        )
        self.assertEqual(result["returned"], 25)
        self.assertIn("def add", result["content"])

    def test_read_file_default_limit(self) -> None:
        result = json.loads(self.tools.read_file("README.md"))
        self.assertEqual(result["returned"], len("# Test Project\n"))

    def test_read_file_forbidden_env(self) -> None:
        result = json.loads(self.tools.read_file(".env"))
        self.assertIn("error", result)
        self.assertIn("security", result["error"])

    def test_read_file_forbidden_key(self) -> None:
        result = json.loads(self.tools.read_file("secret.key"))
        self.assertIn("error", result)
        self.assertIn("security", result["error"])

    def test_read_file_forbidden_pem(self) -> None:
        result = json.loads(self.tools.read_file("cert.pem"))
        self.assertIn("error", result)

    def test_read_file_forbidden_db(self) -> None:
        result = json.loads(self.tools.read_file("data.db"))
        self.assertIn("error", result)

    def test_read_file_env_example_allowed(self) -> None:
        result = json.loads(self.tools.read_file(".env.example"))
        self.assertIn("content", result)
        self.assertIn("SECRET=replace_me", result["content"])

    def test_read_file_traversal_rejected(self) -> None:
        result = json.loads(self.tools.read_file("../outside.txt"))
        self.assertIn("error", result)

    def test_read_file_not_found(self) -> None:
        result = json.loads(self.tools.read_file("nonexistent.py"))
        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    def test_read_file_ignored_dir(self) -> None:
        result = json.loads(self.tools.read_file(".git/config"))
        self.assertIn("error", result)
        self.assertIn("ignored", result["error"])

    # ── search_code ──────────────────────────────────
    def test_search_code_finds_matches(self) -> None:
        result = json.loads(self.tools.search_code("def hello"))
        self.assertGreaterEqual(result["total_count"], 1)
        paths = [m["file"] for m in result["matches"]]
        self.assertIn("src/app.py", paths)

    def test_search_code_scoped_to_dir(self) -> None:
        result = json.loads(self.tools.search_code("add", path="src"))
        self.assertGreaterEqual(result["total_count"], 1)
        paths = [m["file"] for m in result["matches"]]
        self.assertIn("src/utils.py", paths)

    def test_search_code_no_matches(self) -> None:
        result = json.loads(self.tools.search_code("xyznonexistent123"))
        self.assertEqual(result["total_count"], 0)

    def test_search_code_skips_ignored_dirs(self) -> None:
        result = json.loads(self.tools.search_code("module.exports"))
        self.assertEqual(result["total_count"], 0)

    def test_search_code_skips_forbidden_files(self) -> None:
        result = json.loads(self.tools.search_code("SECRET"))
        paths = [m["file"] for m in result["matches"]]
        self.assertIn(".env.example", paths)
        file_matches = [p for p in paths if p.endswith(".env")]
        self.assertEqual(file_matches, [])

    def test_search_code_traversal_rejected(self) -> None:
        result = json.loads(self.tools.search_code("anything", path="../"))
        self.assertIn("error", result)
