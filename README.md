<p>
<img
src="https://raw.githubusercontent.com/longregen/matrix-commander-ng/main/logos/matrix-commander-ng.svg"
alt="matrix-commander-ng logo" height="150">

# matrix-commander-ng

A maintained, actively-developed CLI client for [Matrix](https://matrix.org), written in Rust.

**matrix-commander-ng** is a fork of [matrix-commander-rs](https://github.com/8go/matrix-commander-rs) by [8go](https://github.com/8go), with the goal of becoming a drop-in replacement for the Python [matrix-commander](https://github.com/8go/matrix-commander) with matching output, updated dependencies, and long-term maintenance.

[Test Results](https://longregen.github.io/matrix-commander-ng/) | [Original Project](https://github.com/8go/matrix-commander-rs)

## Quick Start

### With Nix (recommended)

Run directly without installing:

```sh
nix run github:longregen/matrix-commander-ng -- --help
```

Or add to your flake:

```nix
{
  inputs.matrix-commander-ng.url = "github:longregen/matrix-commander-ng";
}
```

Then use `matrix-commander-ng.packages.${system}.default` in your configuration.

### From Source

```sh
git clone https://github.com/longregen/matrix-commander-ng
cd matrix-commander-ng
cargo build --release
./target/release/matrix-commander-ng --help
```

## Usage

```sh
# First-time login
matrix-commander-ng --login password --homeserver https://matrix.example.com

# SSO login (opens browser)
matrix-commander-ng --login sso --homeserver https://matrix.example.com

# Send a message
matrix-commander-ng --message "Hello from the terminal"

# Send to a specific room
matrix-commander-ng --room '!roomid:example.com' --message "Hello"

# Send a file
matrix-commander-ng --room '!roomid:example.com' --file photo.jpg

# Send with markdown formatting
matrix-commander-ng --message "**bold** and _italic_" --markdown

# Listen for new messages
matrix-commander-ng --listen once

# Listen continuously
matrix-commander-ng --listen forever --output json

# Room operations
matrix-commander-ng --room-create "my-room"
matrix-commander-ng --joined-rooms
matrix-commander-ng --joined-members '!roomid:example.com'

# Device management
matrix-commander-ng --devices

# Verification
matrix-commander-ng --verify emoji

# Get room info
matrix-commander-ng --get-room-info '!roomid:example.com' --output json

# Logout
matrix-commander-ng --logout me
```

## What's Different from matrix-commander-rs

matrix-commander-ng brings the Rust implementation to behavioral parity with the Python matrix-commander:

- **Equalized output** -- JSON output format, field names, and structure match the Python version so existing scripts and integrations work unchanged.
- **Updated dependencies** -- matrix-sdk 0.16 (latest), all dependencies current as of March 2026.
- **SSO login** -- Full SSO support via `--login sso`, tested against Dex identity provider.
- **Bug fixes** -- Fixed `--room-unban` (was a broken stub), fixed `--room-leave`/`--room-forget` error messages, fixed `--devices` JSON output.
- **New features** -- `--print-event-id`, `--delete-mxc-before`, emoji shortcode expansion, `--has-permission`.
- **Comprehensive test suite** -- 65 integration tests running in a NixOS VM with a real Synapse server. See them run live at the [test results page](https://longregen.github.io/matrix-commander-ng/).

### Breaking Changes from matrix-commander-rs

If you were using matrix-commander-rs with shell scripts, note that some CLI output has changed to match the Python version's format. Specifically:

- JSON output fields and structure have been standardized
- Some error messages have changed
- `--joined-members` output format differs

Check the [test results page](https://longregen.github.io/matrix-commander-ng/) for exact output examples.

## Platform Support

| Platform | Status |
|----------|--------|
| x86_64-linux | Fully tested (NixOS VM integration tests) |
| aarch64-linux | Builds, not yet integration-tested |
| x86_64-darwin | Builds |
| aarch64-darwin | Builds |

## Integration Tests

The project includes 65 automated integration tests that run inside a NixOS VM with a real Synapse homeserver and Dex SSO identity provider. Tests cover:

- Authentication (login/logout/SSO)
- Room operations (create/join/leave/ban/kick/forget/aliases)
- Messaging (text/markdown/HTML/code/notice/emote/file)
- Users and invites
- Device management and verification
- User profile operations
- Key management and crypto
- Media upload and download
- REST API queries
- Edge cases and error handling

Run the tests locally:

```sh
nix build .#checks.x86_64-linux.integration-test -L
```

View test results with a recording:

```sh
nix build .#pages-site && python3 -m http.server -d result/
```

## Build Performance

The Nix flake uses [crane](https://github.com/ipetkov/crane) for incremental Rust builds:

- **Dependencies** are built separately and cached -- only rebuilt when `Cargo.toml`/`Cargo.lock` change.
- **CI builds** use a fast profile (no LTO, no optimization, mold linker) for ~3 minute cold builds.
- **Release builds** use fat LTO + codegen-units=1 for maximum optimization.

## Project Structure

```
src/
  main.rs          Entry point, CLI dispatch
  args.rs          CLI argument definitions (clap)
  types.rs         Error types, credentials, enums
  cli.rs           Login, verify, and message handling
  mclient.rs       Matrix client operations (rooms, media, REST API)
  listen.rs        Message listening and output formatting
  emoji_verify.rs  Interactive emoji verification
tests/
  nixos-test.nix   NixOS VM integration test suite
scripts/
  log-to-cast.py   Convert test logs to asciicast recordings
  generate-site.py Generate GitHub Pages test results site
```

## Credits

- [8go](https://github.com/8go) -- original author of [matrix-commander](https://github.com/8go/matrix-commander) (Python) and [matrix-commander-rs](https://github.com/8go/matrix-commander-rs) (Rust)
- [matrix-rust-sdk](https://github.com/matrix-org/matrix-rust-sdk) -- the Matrix SDK for Rust

## License

GPL-3.0-or-later (same as the original project)
