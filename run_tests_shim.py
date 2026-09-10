"""A minimal, honest stand-in for pytest, used only because this sandbox's
egress proxy blocks pypi.org (x-deny-reason: host_not_allowed) even though
it's nominally an allowed domain. This shim implements exactly the three
pytest features the test suite actually uses -- @pytest.fixture, pytest.raises,
and the built-in tmp_path fixture -- and nothing else. It does NOT modify the
test files in any way; tests/test_*.py are imported and run completely
unchanged. This is not a replacement for running real pytest and is clearly
disclosed as such in the Test Report.
"""

import inspect
import pathlib
import sys
import tempfile
import traceback
import types


class _FixtureRequest(Exception):
    pass


def fixture(func):
    func._is_fixture = True
    return func


class raises:
    def __init__(self, exc_type):
        self.exc_type = exc_type
        self.value = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            raise AssertionError(f"DID NOT RAISE {self.exc_type.__name__}")
        if not issubclass(exc_type, self.exc_type):
            return False  # let unexpected exception types propagate
        self.value = exc_val
        return True  # suppress the expected exception


# Build a fake 'pytest' module and register it in sys.modules BEFORE the
# test files are imported, so their `import pytest` resolves to this shim.
_shim = types.ModuleType("pytest")
_shim.fixture = fixture
_shim.raises = raises
sys.modules["pytest"] = _shim


def _make_tmp_path():
    return pathlib.Path(tempfile.mkdtemp(prefix="ems_test_"))


class _Runner:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.errors = []

    def run_module(self, module_name, module_path):
        import importlib.util
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        fixtures = {
            name: obj for name, obj in vars(module).items()
            if callable(obj) and getattr(obj, "_is_fixture", False)
        }

        # module-level test_* functions
        for name, obj in vars(module).items():
            if name.startswith("test_") and inspect.isfunction(obj):
                self._run_one(f"{module_name}::{name}", obj, fixtures)

        # Test* classes with test_* methods
        for cls_name, cls in vars(module).items():
            if inspect.isclass(cls) and cls_name.startswith("Test"):
                instance = cls()
                for meth_name in dir(instance):
                    if meth_name.startswith("test_"):
                        bound = getattr(instance, meth_name)
                        self._run_one(f"{module_name}::{cls_name}::{meth_name}", bound, fixtures)

    def _resolve(self, param_name, fixtures, cache, teardowns):
        if param_name in cache:
            return cache[param_name]
        if param_name == "tmp_path":
            value = _make_tmp_path()
            cache[param_name] = value
            return value
        fixture_func = fixtures[param_name]
        sig = inspect.signature(fixture_func)
        kwargs = {p: self._resolve(p, fixtures, cache, teardowns) for p in sig.parameters}
        result = fixture_func(**kwargs)
        if inspect.isgenerator(result):
            value = next(result)
            cache[param_name] = value
            teardowns.append(result)
            return value
        cache[param_name] = result
        return result

    def _run_one(self, test_id, test_callable, fixtures):
        sig = inspect.signature(test_callable)
        cache = {}
        teardowns = []
        try:
            kwargs = {p: self._resolve(p, fixtures, cache, teardowns) for p in sig.parameters}
            test_callable(**kwargs)
            self.passed.append(test_id)
            print(f"PASSED  {test_id}")
        except AssertionError as e:
            self.failed.append((test_id, str(e)))
            print(f"FAILED  {test_id}\n        {e}")
        except Exception as e:
            self.errors.append((test_id, f"{type(e).__name__}: {e}"))
            print(f"ERROR   {test_id}\n        {type(e).__name__}: {e}")
            traceback.print_exc(limit=2)
        finally:
            for gen in reversed(teardowns):
                try:
                    next(gen)
                except StopIteration:
                    pass

    def summary(self):
        total = len(self.passed) + len(self.failed) + len(self.errors)
        print("\n" + "=" * 60)
        print(f"{len(self.passed)} passed, {len(self.failed)} failed, "
              f"{len(self.errors)} errors, out of {total} tests")
        print("=" * 60)
        return len(self.failed) == 0 and len(self.errors) == 0


if __name__ == "__main__":
    import os
    project_root = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(project_root, "src")
    sys.path.insert(0, src_path)

    runner = _Runner()
    test_dir = os.path.join(project_root, "tests")
    for fname in sorted(os.listdir(test_dir)):
        if fname.startswith("test_") and fname.endswith(".py"):
            module_name = fname[:-3]
            print(f"\n--- {fname} ---")
            runner.run_module(module_name, os.path.join(test_dir, fname))

    ok = runner.summary()
    sys.exit(0 if ok else 1)
