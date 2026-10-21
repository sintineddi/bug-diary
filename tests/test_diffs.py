import unittest

from bugdiary import diffs

from .fakes import added_file

SAMPLE = """diff --git a/src/session.ts b/src/session.ts
index 1111111..2222222 100644
--- a/src/session.ts
+++ b/src/session.ts
@@ -1,4 +1,5 @@
 export class Session {
-  token = null;
+  token = null;
+  refreshing = null;
 }
--- a/tail
diff --git a/test/session.test.ts b/test/session.test.ts
new file mode 100644
--- /dev/null
+++ b/test/session.test.ts
@@ -0,0 +1,2 @@
+test("refresh once", () => {});
+-- not a header
diff --git a/logo.png b/logo.png
Binary files a/logo.png and b/logo.png differ
diff --git a/package-lock.json b/package-lock.json
--- a/package-lock.json
+++ b/package-lock.json
@@ -1 +1 @@
-{"a": 1}
+{"a": 2}
"""


class ParseTest(unittest.TestCase):
    def test_files_roles_and_line_numbers(self):
        files = diffs.parse(SAMPLE)
        self.assertEqual(
            [(file.path, file.role) for file in files],
            [
                ("src/session.ts", "code"),
                ("test/session.test.ts", "test"),
                ("logo.png", "noise"),
                ("package-lock.json", "noise"),
            ],
        )
        added = files[0].lines("+")
        self.assertEqual(
            [(line.text, line.new_no) for line in added], [("  token = null;", 2), ("  refreshing = null;", 3)]
        )
        self.assertEqual(files[0].lines("-")[0].old_no, 2)

    def test_hunk_counts_keep_dash_lines_inside_the_hunk(self):
        test_file = diffs.parse(SAMPLE)[1]
        self.assertIsNone(test_file.old_path)
        self.assertEqual(
            [line.text for line in test_file.lines("+")], ['test("refresh once", () => {});', "-- not a header"]
        )

    def test_plain_unified_diff_without_git_headers(self):
        text = "--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-a = 1\n+a = 2\n--- a/y.py\n+++ b/y.py\n@@ -1 +1 @@\n-b\n+c\n"
        self.assertEqual([file.path for file in diffs.parse(text)], ["x.py", "y.py"])

    def test_roles(self):
        self.assertEqual(diffs.file_role("CHANGELOG.md"), "notes")
        self.assertEqual(diffs.file_role("docs/guide.md"), "docs")
        self.assertEqual(diffs.file_role("lib/test_utils.py"), "test")
        self.assertEqual(diffs.file_role("pkg/client_test.go"), "test")
        self.assertEqual(diffs.file_role("src/app.spec.tsx"), "test")
        self.assertEqual(diffs.file_role("node_modules/x/index.js"), "noise")
        self.assertEqual(diffs.file_role("src/latest.js"), "code")


class RenderTest(unittest.TestCase):
    def test_budget_trims_context_then_drops_files(self):
        body = "\n".join(f" line {index}" for index in range(200))
        text = f"--- a/big.py\n+++ b/big.py\n@@ -1,201 +1,201 @@\n{body}\n-old\n+new\n"
        files = diffs.parse(text + text.replace("big.py", "other.py"))
        trimmed = diffs.render(files, 400)
        self.assertIn("+new", trimmed)
        self.assertIn("...", trimmed)
        self.assertLessEqual(len(diffs.render(files[:1], 10_000)), 10_000)
        tiny = diffs.render(files, 70)
        self.assertIn("more changed files not shown", tiny)


class FitTest(unittest.TestCase):
    def test_fit_names_the_files_it_could_not_show(self):
        files = diffs.parse(added_file("a.ts", 70) + added_file("b.ts", 70))
        self.assertEqual(diffs.fit(files, 100_000)[1], [])
        text, unread = diffs.fit(files, 6_000)
        self.assertEqual(unread, ["b.ts"])
        self.assertIn("1 more changed files not shown: b.ts", text)
        self.assertEqual(diffs.fit(files[:1], 1_000)[1], ["a.ts"])


class FindLinesTest(unittest.TestCase):
    def test_matches_added_lines_loosely_and_ignores_short_quotes(self):
        files = diffs.parse(SAMPLE)
        hits = diffs.find_lines(["+   refreshing   =   null;", "}", "not in the diff at all"], files)
        self.assertEqual(hits, [diffs.Hit("src/session.ts", 3, "refreshing = null;")])

    def test_kinds_select_removed_lines(self):
        files = diffs.parse(SAMPLE)
        self.assertEqual(diffs.find_lines(['{"a": 1}'], files, "-")[0].path, "package-lock.json")
        self.assertEqual(diffs.find_lines(['{"a": 1}'], files, "+"), [])


if __name__ == "__main__":
    unittest.main()
