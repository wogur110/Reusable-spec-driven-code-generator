# Retained server desktop contract

CHG-002 adds an optional management interface around the retained server. This file specifies retained server behavior, not an extension to the client wire protocol or a generated-client target. Implementation and verification status is recorded in docs/STATUS.md.

## Launch and scope

`python3 server/gui.py` opens a window titled **Local Messenger - Server**, initially stopped. Optional `--port` (default 8765, 0 allocates a port) and `--static-dir` (default repository-relative generated/typescript-web/dist) prefill controls. `--help` requires no display. Tk/Tcl 8.6 and an interactive display are required; reuse CHG-001 native dependencies. No pip dependency. Running server operations after launch needs no terminal interaction. The existing `server/main.py` CLI and its ready JSON remain compatible and display-free.

Bind only 127.0.0.1. Keep the existing protocol, in-memory streams, idempotency, static serving, and limits. No remote management endpoint, server database, or extra client messages. Both launchers use the same Server/Handler implementation. Clients require no behavioral changes or targeted regeneration; clean regeneration must still pass the expanded retained suite.

## Controls and lifecycle

Show editable Port and Browser assets directory, Start, Stop, Open browser, status, listening URL, session ID, accepted-message count, request/error counts, recent request activity, and accepted-message list with exact full-text details on selection. A visible session notice states: stopping or closing discards server messages; every Start creates a new session requiring fresh/reset client stores. Stop and window close are explicit session-ending actions; no confirmation dialog is required.

Port must be a decimal integer 0–65535; reject bad input visibly before binding. Browser directory must contain index.html; missing build/directory fails visibly before binding with build guidance. Bind errors leave this window able to retry and never stop another process. Disable configuration/Start during starting, running, or stopping; enable Stop/Open browser only when running. Open browser uses the displayed loopback URL and reports launch failure visibly.

States are Stopped, Starting, Running, Stopping, and Error. Repeated clicks cannot create overlapping listeners. Startup and shutdown do not block Tk. Run serve_forever outside the Tk thread; only the Tk thread touches widgets. Stop disables actions, stops accepting requests, closes the listener, and releases resources within six seconds. Window close while stopped, starting, running, or stopping also completes within six seconds, including an idle/partial HTTP request. Only owned server resources are closed. A fresh Start clears all prior session counters/messages and assigns a new session ID. Stop clears monitoring content and listening URL; no old session is presented as live.

## Monitoring

Refresh within one second while running. Count completed HTTP responses and responses with status >=400 (all routes); describe counts as responses, not online clients or deliveries. Count accepted messages once per sender/message ID, not exact replay; show sender, recipient, ID, recipient sequence, and text. Recent request activity is bounded to the latest 200 responses (method, path without query, status). The message table shows at most the latest 200 unique accepted messages while its count includes the complete session. Use scrolling and an exact text detail pane; no truncation of selected text. HTTP threads record data under locks; GUI takes bounded snapshots, never iterates a mutating store or changes message delivery state. Monitoring must not consume messages, advance cursors, or affect idempotency. Session monitoring is local and not persisted.

## Retained automation contract

`server.gui.ServerApp(root, port=8765, static_dir=None)` builds the production controls; main launches this same class. `app.widgets` exposes actual widgets: port-input, static-input, start-button, stop-button, open-browser, server-status, server-url, session-id, session-notice, error-message, message-count, response-count, error-count, messages, message-detail, requests. The messages Treeview has columns sender, recipient, message_id, sequence, text; requests columns method, path, status. Read-only observation is permitted; tests invoke real widget actions, not internal start/stop methods. Window closing exercises the production WM_DELETE_WINDOW callback. Existing client drivers remain independent.

## CHG-003 Users view

The registered [DIRECTORY.md](DIRECTORY.md) contract adds a shared directory and observational per-user Sent/Received/Queued views with filtering and refresh. It defines cumulative durable receipt reports and the exact new GUI controls. Preserve this document’s lifecycle, startup, error, close and global Overview contracts. The selected user activity comes from one locked snapshot; Stop/Start clears all directory/receipt observations.
