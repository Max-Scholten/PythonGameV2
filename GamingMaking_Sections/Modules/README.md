Plugins
=======

Place plugins under Modules/plugins/<plugin_name>/plugin.py

Plugin API
----------
A plugin is a simple Python module exposing one or more hook functions. Hooks are plain callables with names like:

- on_all_lives_lost(player, joystick, screen)
- on_round_end(player1, player2, screen)

Hooks are optional — the plugin manager will call them only when present. If a hook returns a truthy value the manager treats it as "handled".

Examples
--------
See the `ejection` plugin directory for a concrete example of `on_all_lives_lost`.

Safety
------
The plugin manager swallows exceptions raised in plugins so a faulty plugin won't crash the game. Be careful when importing heavy libraries in plugins.

