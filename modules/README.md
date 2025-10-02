# Coman Modules Package

The ``modules`` package hosts the feature plugins that extend the Coman core.
Each module inherits from ``coman.core.base_module.BaseModule`` and can register
API endpoints, background workers, and capability metadata that the orchestrator
exposes through the FastAPI layer.

## Available modules

| Module | Purpose |
| ------ | ------- |
| ``analysis_module`` | Simple analytics pipeline with capability registration |
| ``defense_system`` | Demonstration defensive automation hooks |
| ``integration`` | Example integration surface used by the unit tests |
| ``logic_app`` | Glue logic for external logic apps |
| ``logic_module`` | Rule engine showcase |
| ``manager`` | Resource orchestration helpers |
| ``orchestrator`` | Registers composite workflows with the core |
| ``resource_manager`` | Asset and dependency tracking |
| ``speech_module`` | Speech synthesis/recognition placeholders |
| ``telegram_module`` | Telegram bot wiring reused by the CLI |
| ``text_module`` | Text processing helpers |
| ``ui`` | Static UI bundle that can be mounted into the FastAPI app |
| ``webscraper_module`` | Basic scraping utilities |

Each folder follows the same convention:

```
modules/<module_name>/
    __init__.py
    module.py        # entry point that exposes a ``Module`` subclass
    ...              # supporting files/resources
```

## Running services from the package

Use the unified CLI to load the modules and start the services that depend on
them:

```bash
python -m coman.modules.main api       # FastAPI core with all registered modules
python -m coman.modules.main telegram  # Telegram bot runner
python -m coman.modules.main all       # Run both concurrently
python -m coman.modules.main modules   # List available modules and operations
python -m coman.modules.main call analysis frequency --arg text="hello world"
```

The CLI loads every module via ``coman.core.registry.load_modules`` and exposes
the resulting FastAPI application.  Custom modules that follow the same
structure can be dropped into this folder and will be discovered automatically.
When invoking modules from the console the CLI reuses the same module
implementations that power the API, so business logic only needs to be defined
once.  Arguments for ``call`` can be provided either as ``key=value`` pairs or
via ``--json`` with a full payload.

## Adding a new module

1. Create a new directory under ``modules/`` with an ``__init__.py`` file.
2. Implement a ``module.py`` that exposes a ``Module`` class inheriting from
   ``BaseModule``.
3. Register any API routes, dependencies, or background tasks inside the module.
4. Re-run ``python -m coman.modules.main api`` to see the module available via
   the HTTP API.
