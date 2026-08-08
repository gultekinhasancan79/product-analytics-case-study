from __future__ import annotations

import argparse
import json
from pathlib import Path


def execute_notebook(path: Path) -> int:
    """Parse and execute code cells without adding a Jupyter runtime dependency."""
    notebook = json.loads(path.read_text(encoding="utf-8"))
    if notebook.get("nbformat") != 4:
        raise ValueError("expected nbformat 4 notebook")

    namespace: dict[str, object] = {"__name__": "__notebook__"}
    executed = 0
    for index, cell in enumerate(notebook.get("cells", []), start=1):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        compile(source, f"{path}#cell-{index}", "exec")
        exec(source, namespace)
        executed += 1

    if executed == 0:
        raise ValueError("notebook contains no executable code cells")
    return executed


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute notebook code cells on the tested Python path.")
    parser.add_argument(
        "path",
        type=Path,
        nargs="?",
        default=Path("notebooks/experiment_walkthrough.ipynb"),
    )
    args = parser.parse_args()
    executed = execute_notebook(args.path)
    print(f"NOTEBOOK: PASS ({executed} code cells executed)")


if __name__ == "__main__":
    main()
