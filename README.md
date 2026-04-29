# Bambu printers status dashboard

The tool allows to start a server to monitor the state of the Bambu printers in the workshop.

## Usage

You can it on your machine using the following after cloning the repo:

```bash
cd bambu-dashboard
uv sync
uv run main.py
```

or if you don't have uv:

```bash
cd bambu-dashboard
python -m pip install -r requirements.txt
python main.py
```

