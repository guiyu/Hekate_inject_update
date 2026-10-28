# Upstream source

`fusee_launcher.py` is an unmodified copy from:

- Project: https://github.com/nh-server/fusee-interfacee-tk
- Commit: `fc1497e30c95db83d112899de22057590f039940`
- File SHA-256: `53050630b6100566ea79c53b9c7d7ce0054434b6adec156e5025cf3b4ced9509`
- License: GNU GPL v2, retained in `LICENSE` and in the source header.

The intermezzo binary is not tracked. `prepare_runtime.py` downloads it from the same pinned upstream commit and verifies its recorded SHA-256. Hekate and fusee payloads are also downloaded separately rather than redistributed here.
