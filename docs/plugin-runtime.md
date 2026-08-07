# Plugin Runtime

Sandboxed plugin execution with lifecycle management.

## Plugin Lifecycle

1. **Install** — download and extract plugin package
2. **Enable** — activate plugin in the runtime
3. **Execute** — run plugin in sandboxed environment
4. **Disable** — deactivate without removing
5. **Uninstall** — remove plugin and cleanup

## Plugin Manifest

```json
{
  "name": "filesystem",
  "version": "1.0.0",
  "description": "File system operations",
  "capabilities": ["read", "write", "list"],
  "entry_point": "main.py"
}
```

## Sandboxing

- Isolated execution environment
- Resource quotas (CPU, memory, time)
- Capability-based access control
- No direct access to host filesystem

## Marketplace

Plugins can be published to and installed from the ARKON marketplace.
