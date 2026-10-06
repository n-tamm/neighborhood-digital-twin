# Scripts

Scripts provide short, repeatable entry points for operations such as downloading one approved source, building a pilot dataset, running an experiment, exporting a serving bundle, or checking a deployment.

Keep scripts thin. Parsing, validation, transformations, and modeling logic belong in `src/neighborhood_twin/`, where they can be imported and tested. A script should mainly load configuration, call package functions, report progress, and return a useful exit code.

Every script should support a small or dry-run path when practical. Destructive or expensive operations should require explicit targets rather than broad defaults.
