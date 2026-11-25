# Local stdio launcher (this fork only)

Runs the gateway as a **stdio MCP server** for one Substack account, with the
`substack.sid` session cookie kept in the macOS Keychain. It has no HTTP listener.

## Store or rotate the cookie

```bash
security add-generic-password -U -s substack-gateway -a substack.sid -w
```

It prompts for the value, so the value never lands in shell history. The cookie
is full-account access for about 90 days. Re-run the command after it expires or
after a Substack logout. Never put it in a file, an env var or a chat.

## Run

```bash
local/substack-gateway-stdio.sh                    # drafts and reads only
local/substack-gateway-stdio.sh --allow-schedule   # adds schedule/unschedule
```

MCP client config (stdio): `command` = absolute path of the launcher.

## Guarantees and limits

- The cookie goes Keychain → pipe on fd 3 → the gateway process, which reads it
  once and closes the descriptor. It never appears in argv, the environment, a
  file or a log.
- No listening socket. The single-account credential resolver is safe only
  because the transport is stdio.
- Unregistered on purpose: notes, comments, replies, likes and restacks (all of
  them write in public immediately). There is no publish tool. Scheduling needs
  `--allow-schedule`.
- Residual: any process running as this macOS user can still read the Keychain
  item with `security`. Substack offers no scoped credential, so this can be
  bounded but not closed.

## Re-qualify (G6a Q1–Q5)

```bash
.venv/bin/python local/g6a_probe.py --days 30
```

The probe creates one marked draft, reads it, finds it, schedules it 30 days
out, unschedules it and deletes it. It publishes nothing.
