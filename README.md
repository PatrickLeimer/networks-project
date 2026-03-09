Please use a virtual environment to manage dependencies. You can create one using the following command:

```bash
    python -m venv .venv
```

After creating the virtual environment, activate it using the appropriate command for your operating system:

- On Windows:
```bash
    .venv\Scripts\activate
```

- On macOS and Linux:
```bash
    source .venv/bin/activate
```

you should see the name of your virtual environment in your terminal prompt, indicating that it is active. Once the virtual environment is activated, you can install the required dependencies using pip:

```bash
    pip install -r requirements.txt
```





# Here is a basic plan and file structure for what we will be doing in this project:
Feel free to modify. This is just a starting point to help organize. Just please document where you want to change things so we can keep track of it.

```
project/
│
├── peerProcess.py # main program entry point
│
├── config/ # configuration parsing
│   └── config_loader.py
│
├── networking/ # TCP server and connection handling
│   ├── server.py
│   ├── client.py
│   └── connection_manager.py
│
├── protocol/ # message definitions and encoding/decoding
│   ├── message.py
│   ├── message_types.py
│   ├── encoder.py
│   └── decoder.py
│
├── p2p/ # peer logic and neighbor management
│   ├── peer.py
│   ├── peer_manager.py
│   ├── neighbor_state.py
│   └── choking_manager.py
│
├── file_manager/ # file piece handling
│   ├── piece_manager.py
│   └── bitfield.py
│
└── utils/ # add any necessary utilities
```
