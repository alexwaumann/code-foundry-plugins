# code-foundry-plugins

The default plugin registry for [Code Foundry](https://github.com/alexwaumann/code-foundry).
Code Foundry reads `index.json` from every registry in its `plugins.registries` setting
and lists the plugins under **Settings → Plugins → Browse**. `plugin install <name>`
downloads the release tarball, verifies its SHA-256 and installs it under
`~/.code-foundry/plugins/<name>`; the user consents to the manifest's permissions before
the plugin ever runs.

## Adding or updating a plugin

1. Cut a GitHub release in the plugin's repository with one tarball per platform:
   `<name>-<version>-darwin-arm64.tar.gz` and `<name>-<version>-darwin-amd64.tar.gz`.
   Each tarball contains the package directory contents at its root: `plugin.json`
   (the manifest) and the executable the manifest's `exec` points at.
2. Add or edit `plugins/<name>.json` (schema below) and open a pull request.
3. CI re-downloads each tarball, checks the SHA-256, reads `plugin.json` out of it and
   checks that the name, version and permissions match the entry. When the PR merges, CI
   regenerates `index.json` on `main`.

Entries are owned by whoever maintains the plugin repository. A registry for a workplace
is the same layout in a private repository; `gh` auth covers it.

## Entry schema (`plugins/<name>.json`)

```json
{
  "name": "gh-actions",
  "displayName": "GitHub Actions",
  "description": "Runs, jobs and failed-step logs for the selected thread's pull request.",
  "repo": "alexwaumann/code-foundry-plugin-gh-actions",
  "version": "0.1.0",
  "protocol": 1,
  "permissions": {
    "commands": ["thread.send", "view.open.url", "pr.checks"],
    "events": ["gh", "thread"],
    "threadStatus": true,
    "sessionEnv": false,
    "secrets": false,
    "threads": false,
    "terminals": false,
    "api": false
  },
  "artifacts": {
    "darwin/arm64": {
      "url": "https://github.com/alexwaumann/code-foundry-plugin-gh-actions/releases/download/v0.1.0/gh-actions-0.1.0-darwin-arm64.tar.gz",
      "sha256": "…"
    },
    "darwin/amd64": {
      "url": "https://github.com/alexwaumann/code-foundry-plugin-gh-actions/releases/download/v0.1.0/gh-actions-0.1.0-darwin-amd64.tar.gz",
      "sha256": "…"
    }
  }
}
```

* `name` is the manifest's `name`: `[a-z0-9][a-z0-9-]{0,63}`, and the file name.
* `version` is strict semver without a leading `v`; the release tag is `v<version>`.
* `permissions` must equal the manifest's `permissions` block (missing keys read as
  false / empty), so Browse can show what a plugin will do before download.
* `artifacts` lists at least `darwin/arm64`. Code Foundry is macOS-only today.

## `index.json`

Generated. `{ "schema": 1, "generatedAt": "<RFC 3339>", "plugins": [ <entry>, … ] }`,
entries sorted by `name`. Clients must tolerate unknown fields.
