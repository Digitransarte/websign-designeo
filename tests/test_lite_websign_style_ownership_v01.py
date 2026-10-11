"""Lite/Websign plugin stylesheet ownership, CSS and PHP hooks smoke tests."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import re
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_lite_core_library_v01 import _load
from scripts.build_lite_dynamic_core_v01 import FRONT_CSS, EDITOR_CSS
from scripts.audit_lite_css_cascade_v01 import parse_css, build_cascade_safe_core
from scripts.build_lite_websign_style_ownership_v01 import (
    build_style_ownership_core, FUNCTIONS, HOOK_MARKER, CSS_MARKER
)


class LiteWebsignStyleOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = TemporaryDirectory()
        cls.candidate_path = Path(cls.folder.name) / "new-theme.zip"
        cls.old_path = Path(cls.folder.name) / "old-theme.zip"
        cls.report = build_style_ownership_core(ROOT, cls.candidate_path)
        build_cascade_safe_core(ROOT, cls.old_path)
        cls.new = _load(cls.candidate_path)
        cls.old = _load(cls.old_path)

    @classmethod
    def tearDownClass(cls):
        cls.folder.cleanup()

    def test_only_theme_php_and_front_editor_css_changed(self):
        self.assertEqual(len(self.new), 16)
        self.assertEqual(set(self.new), set(self.old))
        modified = {n for n in self.new if self.new[n] != self.old[n]}
        self.assertEqual(modified, {FUNCTIONS, FRONT_CSS, EDITOR_CSS})
        self.assertEqual(self.report["unchanged_files"], 13)
        self.assertFalse(self.report["plugin_source_modified"])
        self.assertFalse(self.report["release_ready"])

    def test_theme_only_dequeues_expected_plugin_handle_with_late_priority(self):
        code = self.new[FUNCTIONS].decode("utf-8")
        self.assertEqual(code.count(HOOK_MARKER), 1)
        self.assertEqual(code.count("wp_dequeue_style( 'websign-runtime' );"), 1)
        self.assertIn("function designeo_lite_own_websign_styles()", code)
        for hook in ("wp_enqueue_scripts", "enqueue_block_editor_assets"):
            self.assertIn(
                f"add_action( '{hook}', 'designeo_lite_own_websign_styles', 1000 );",
                code
            )
        self.assertNotIn("wp_deregister_style", code)
        self.assertNotIn("remove_action( 'wp_enqueue_scripts', 'websign", code)
        self.assertNotIn("deactivate_plugins", code)

    def test_mobile_css_fallback_preserves_websign_layout(self):
        for name in (FRONT_CSS, EDITOR_CSS):
            css = self.new[name].decode("utf-8")
            original = self.old[name].decode("utf-8")
            self.assertEqual(css.count(CSS_MARKER), 1)
            self.assertEqual(css.count("!important"), original.count("!important"))
            self.assertIn(".wp-block-columns.websign-columns-gap-normal", css)
            self.assertIn("flex-direction: column", css)
            self.assertIn("flex-basis: auto", css)
            self.assertNotIn("http://", css)
            self.assertGreater(len(parse_css(css)), 5)

    def test_build_is_deterministic_and_fails_on_overwrite(self):
        with TemporaryDirectory() as td:
            other = Path(td) / "theme.zip"
            build_style_ownership_core(ROOT, other)
            self.assertEqual(other.read_bytes(), self.candidate_path.read_bytes())
            with self.assertRaises(FileExistsError):
                build_style_ownership_core(ROOT, other)

    def test_rejects_output_inside_original_repo(self):
        with self.assertRaises(ValueError):
            build_style_ownership_core(ROOT, ROOT / "do-not-create.zip")

    @unittest.skipUnless(shutil.which("php"), "PHP CLI required for runtime hook simulation")
    def test_php_syntax_and_frontend_editor_hook_order(self):
        with TemporaryDirectory() as td:
            file = Path(td) / "functions.php"
            file.write_bytes(self.new[FUNCTIONS])
            lint = subprocess.run(["php", "-l", str(file)],
                                  capture_output=True, text=True, check=False)
            self.assertEqual(lint.returncode, 0, lint.stdout + lint.stderr)

            # WordPress-like isolated stub: plugin enqueues at priority 10;
            # active Lite theme dequeues at 1000 on both hooks. No live WP.
            stub = Path(td) / "hooks.php"
            stub.write_text(r"""<?php
define('ABSPATH', '/synthetic/');
$GLOBALS['hooks'] = [];
$GLOBALS['enqueued'] = [];
function add_action($hook, $callback, $priority = 10) {
    $GLOBALS['hooks'][$hook][$priority][] = $callback;
}
function add_filter($h, $c, $p = 10) {}
function remove_action($h, $c, $p = 10) {}
function remove_filter($h, $c, $p = 10) {}
function wp_get_theme() {
    return new class { function get($name) { return '2.0.1'; } };
}
function get_template_directory_uri() { return 'http://localhost/synthetic'; }
function wp_enqueue_style($handle, $uri, $deps = [], $version = null) {
    $GLOBALS['enqueued'][] = $handle;
}
function wp_enqueue_script($handle, $uri, $deps = [], $version = null, $args = []) {}
function wp_dequeue_style($handle) {
    $GLOBALS['enqueued'] = array_values(array_filter(
        $GLOBALS['enqueued'], fn($h) => $h !== $handle
    ));
}
add_action('wp_enqueue_scripts', function() {
    $GLOBALS['enqueued'][] = 'websign-runtime';
}, 10);
add_action('enqueue_block_editor_assets', function() {
    $GLOBALS['enqueued'][] = 'websign-runtime';
}, 10);
require __DIR__ . '/functions.php';
function dispatch_style_hook($name) {
    $GLOBALS['enqueued'] = [];
    ksort($GLOBALS['hooks'][$name], SORT_NUMERIC);
    foreach ($GLOBALS['hooks'][$name] as $callbacks) {
        foreach ($callbacks as $cb) { $cb(); }
    }
    return $GLOBALS['enqueued'];
}
foreach (['wp_enqueue_scripts','enqueue_block_editor_assets'] as $hook) {
    if (in_array('websign-runtime', dispatch_style_hook($hook), true)) {
        fwrite(STDERR, $hook . ' plugin not dequeued');
        exit(1);
    }
}
if (!isset($GLOBALS['hooks']['wp_enqueue_scripts'][1000]) ||
    !isset($GLOBALS['hooks']['enqueue_block_editor_assets'][1000])) {
    exit(2);
}
echo 'FRONT_EDITOR_DEQUEUE_OK';
""", encoding="utf-8")
            result = subprocess.run(["php", str(stub)],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("FRONT_EDITOR_DEQUEUE_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
