# AGENTS.md

## Cursor Cloud specific instructions

This is a greenfield repository ("scoreflow") with no application code yet. As of the initial setup:

- **No languages/frameworks/package managers** are configured. When code is added, update this section and the VM update script accordingly.
- **No services** need to be started.
- **No lint, test, or build commands** are available.
- The only existing file is `README.md`.

When the first application code is committed, future agents should:
1. Re-run environment setup to install the chosen language runtime and dependencies.
2. Update the VM update script (via `SetupVmEnvironment`) with the appropriate dependency-install commands.
3. Update this section with service startup instructions, lint/test/build commands, and any non-obvious caveats discovered during setup.
