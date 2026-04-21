# Networks Project

This repository contains a peer-to-peer file sharing project with:

- TCP peer connections
- handshake and message encoding/decoding
- bitfield exchange
- one receive loop per connected neighbor
- per-neighbor state tracking
- piece storage and bitfield tracking
- spec-style event logging

The project is currently in progress. The networking and state-management foundation is in place, while the full request/piece flow, choking manager, and termination logic are still being finished.

## Current State

Implemented:

- config loading from `Common.cfg` and `PeerInfo.cfg`
- peer startup through `peerProcess.py`
- inbound and outbound TCP connection handling
- handshake validation
- synchronized initial bitfield exchange after handshake
- initial interested / not interested exchange
- `NeighborState` tracking for:
  - remote bitfield
  - choke state
  - interest state
  - bytes downloaded during an interval
- one `PeerConnection` receive thread per neighbor
- decoding and dispatching of:
  - choke
  - unchoke
  - interested
  - not interested
  - have
  - bitfield
  - request
  - piece
- piece ownership tracking through `PieceManager`
- file logging through `file_manager/logger.py`
- socket address reuse on the TCP server for easier local reruns

Not finished yet:

- request flow after unchoke
- sending actual piece data in response to requests
- broadcasting `HAVE` after new pieces are downloaded
- choking / unchoking manager
- optimistic unchoking
- clean global termination when all peers complete the file

## Project Layout

```text
peerProcess.py              Main entry point for each peer
config/                     Config parsing
file_manager/               Bitfield, piece storage, logger
networking/                 Client, server, connection manager
p2p/                        Neighbor state and per-peer receive loop
protocol/                   Handshake, messages, encoders, decoders
local_testing/              Local config and test file
docs/                       Project PDF
```

Important files:

- `peerProcess.py`
- `networking/connection_manager.py`
- `networking/server.py`
- `p2p/neighbor_state.py`
- `p2p/peer_connection.py`
- `file_manager/piece_manager.py`
- `file_manager/logger.py`

## Environment Setup

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

Windows:

```bash
.venv\Scripts\activate
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Local Test Configuration

The current local test setup is:

`local_testing/Common.cfg`

```text
NumberOfPreferredNeighbors 1
UnchokingInterval 5
OptimisticUnchokingInterval 10
FileName local_testing/thefile
FileSize 2167705
PieceSize 16384
```

`local_testing/PeerInfo.cfg`

```text
1001 localhost 6001 1
1002 localhost 6002 0
1003 localhost 6003 0
```

That means:

- peer `1001` starts with the full file
- peers `1002` and `1003` start without the file
- peers communicate over ports `6001`, `6002`, and `6003`

## How To Run

Run each peer in its own terminal from the repository root.

Terminal 1:

```bash
python peerProcess.py 1001
```

Terminal 2:

```bash
python peerProcess.py 1002
```

Terminal 3:

```bash
python peerProcess.py 1003
```

## How To Stop

Use `Ctrl+C` in each terminal to stop peers cleanly.

This is important because:

- the logger now flushes and closes on normal shutdown
- clean shutdown gives the best chance of avoiding partially written log files
- force-killing processes can still leave ports busy for a bit or skip cleanup entirely

## Logs

Each peer writes a log file named:

```text
log_peer_<peer_id>.log
```

Examples:

- `log_peer_1001.log`
- `log_peer_1002.log`
- `log_peer_1003.log`

The logger is currently wired for these spec-style events:

- outgoing connection
- incoming connection
- choke
- unchoke
- interested
- not interested
- have
- piece download
- complete file

At the current project state, the most common visible log events are:

- connection made
- connected from
- interested
- not interested

You will not see full piece-download behavior yet until the request/piece flow is implemented.

## Rerunning Locally

The server now enables socket address reuse, which makes quick reruns easier after a normal shutdown.

Recommended rerun workflow:

1. Stop all peers with `Ctrl+C`
2. Wait a moment for terminals to return
3. Start the peers again

If you still hit a Windows port-in-use error like `WinError 10048`, an old Python process is probably still running. In PowerShell:

```powershell
Get-Process -Name python | Stop-Process -Force
```

Then restart the peers.

## Current Testing Tips

Good smoke tests right now:

- start all three peers and confirm connections are established
- check that log files are created
- verify peers log interested / not interested events
- verify rerunning after `Ctrl+C` works more reliably than before

Useful PowerShell commands:

```powershell
Get-Content log_peer_1001.log
Get-Content log_peer_1002.log
Get-Content log_peer_1003.log
```

## Known Limitations

- peers do not yet complete a full file transfer
- request and piece handlers still contain TODOs
- there is no finished choking manager yet
- there is no finished optimistic unchoking yet
- the main loop does not yet terminate automatically when all peers finish
- force-killing peers can still cause messy local state during testing

## Notes For Team

- run commands from the repository root
- local test files such as `peer_*` directories and `*.log` files are ignored by `.gitignore`

## Next Major Milestones

- implement request flow in `p2p/peer_connection.py`
- implement piece upload flow in `p2p/peer_connection.py`
- add choking manager logic
- add termination detection in `peerProcess.py`
