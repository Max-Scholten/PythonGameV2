"""Simple plugin manager.
Plugins live under Modules/plugins/<plugin_name>/plugin.py and can expose hook functions.
A hook is any callable named like on_all_lives_lost, on_round_end, etc.
This manager discovers and loads plugins, and provides run_hook(hook_name, *args, **kwargs)
that calls each plugin hook and returns True if any plugin returned truthy.
"""
import os
import importlib.util

PLUGINS_DIR = os.path.join(os.path.dirname(__file__), "plugins")
_loaded = []


def _load_plugin_from_path(path):
    name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(f"modules.plugins.{name}", path)
    if spec is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None


def discover_plugins():
    """Discover plugin modules under Modules/plugins/*/plugin.py."""
    global _loaded
    plugins = []
    if not os.path.isdir(PLUGINS_DIR):
        return plugins
    for entry in os.listdir(PLUGINS_DIR):
        pdir = os.path.join(PLUGINS_DIR, entry)
        if not os.path.isdir(pdir):
            continue
        candidate = os.path.join(pdir, "plugin.py")
        if os.path.isfile(candidate):
            mod = _load_plugin_from_path(candidate)
            if mod:
                plugins.append(mod)
    _loaded = plugins
    return plugins


def run_hook(hook_name, *args, **kwargs):
    """Run named hook across all loaded plugins. Returns True if any plugin returned truthy."""
    if not _loaded:
        discover_plugins()
    result = False
    for mod in _loaded:
        fn = getattr(mod, hook_name, None)
        if callable(fn):
            try:
                r = fn(*args, **kwargs)
                if r:
                    result = True
            except Exception:
                # plugin errors should not crash the game; ignore them
                pass
    return result

