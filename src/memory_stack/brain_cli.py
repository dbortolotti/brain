from __future__ import annotations

import typer

from memory_stack.evals.cli import app as eval_app


app = typer.Typer(no_args_is_help=True)
app.add_typer(eval_app, name="eval")


if __name__ == "__main__":
    app()

