# Bambu printers status dashboard

The tool allows to start a server to monitor the state of the Bambu printers in the workshop.

<img width="1738" height="1036" alt="image" src="https://github.com/user-attachments/assets/86c23deb-336e-4acf-ba7c-c857ce6149d9" />


## Usage

If you are connected to the company network, you shold only need to go to this page: http://192.168.10.117:8080/

### Local run
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

