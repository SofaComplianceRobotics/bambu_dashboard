# Bambu Lab Print Farm Dashboard

A local dashboard to monitor all Bambu Lab printers in real time — temperatures, progress, layers, and status — all in one browser tab.

---

## Requirements

- A Windows PC on the same local network the printers
- Node.js installed on your machine
- LAN Mode enabled on each Bambu Lab printer

---

## Step 1 — Install Node.js

1. Go to **https://nodejs.org**
2. Click the **LTS** download button (the left one, recommended for most users)
3. Run the installer and click through with all default options

---

## Step 2 — Enable LAN Mode on your printers

On each printer you want to monitor:

1. Open the **Bambu Lab app** on your phone or PC
2. Go to your printer → **Settings** → **LAN Mode**
3. Toggle LAN Mode **on**

---

## Step 3 — Configure your printers

Open `server.js` in any text editor (Notepad is fine) and find this section near the top:

```js
const PRINTERS = [
  { id: 0, name: "Printer 1", ip: "192.168.10.102", serial: "00M09A3B2700035", code: "cfda32ee" },
  { id: 1, name: "Printer 2", ip: "192.168.10.106", serial: "00M09D482400921", code: "6e144d6b" },
  { id: 2, name: "Printer 3", ip: "192.168.10.103", serial: "00M09D490201428", code: "fdc70620" },
  { id: 3, name: "Printer 4", ip: "192.168.10.104", serial: "00M09C431200531", code: "f73bb784" },
];
```

Fill in each printer's details:

| Field | Where to find it |
|---|---|
| `name` | Any label you want, e.g. `"Workshop P1S"` |
| `ip` | Your printer's local IP — check your router's device list or the Bambu app under Device → Settings |
| `serial` | Bambu app → Device → Settings → Serial Number |
| `code` | Bambu app → Device → Settings → LAN Mode → Access Code |

You can have as many lines as you want.

---

## Step 4 — Launch the dashboard

Double-click **`start_dashboard.bat`**

- On first run it will install dependencies automatically (takes ~30 seconds, only happens once)
- Your browser will open the dashboard automatically
- Keep the black console window open — closing it stops the server
- The first time running it if it only installed the dependencies but did not launch the window, then just relaunch the .bat

---

## Troubleshooting

**Window opens and closes instantly**
Make sure Node.js is installed correctly. Open a Command Prompt and run `node --version`. If it says "not recognized", reinstall Node from nodejs.org and make sure to check "Add to PATH" during installation.

**Printer shows "Not authorized"**
The Access Code is wrong. Open the Bambu app, go to LAN Mode and copy the code again — it changes every time you toggle LAN mode off and on.

**Printer shows "connack timeout"**
The IP address is wrong or the printer is offline. Check your router's connected devices list to find the correct IP, and make sure LAN Mode is enabled on that printer.

**Dashboard doesn't open in browser**
Open `dashboard.html` manually in your browser. It's in the `bambu_dashboard` folder. The server must be running (console window open) for it to show live data.

---

## Stopping the dashboard

Just close the black console window, or press `Ctrl+C` inside it.

## Seeing more data

If you wish to see more info on the printers, here is a post i found on a form that lists the diferent infos you could show, i did not bother to look furter into their question marks

https://community.home-assistant.io/t/bambu-lab-x1-x1c-mqtt/489510/165
```
"ams_rfid_status": 0,  // ??? - I assume when it's actively reading something but cannot confirm.
        "ams_status": 0,  // ???
        "bed_target_temper": 0.0,  // Target Bed Temp
        "bed_temper": 18.0,  // Current Bed Temp
        "big_fan1_speed": "0",  // Aux Fan
        "big_fan2_speed": "0",  // Chamber Fan
        "chamber_temper": 25.0, // Chamber Temp
        "command": "push_status",  // push_status is the main receive command. There are many other commands, some receive only, some work both ways.
        "cooling_fan_speed": "0", // Part Cooling Fan - on the magnetic cover of hotend but not hotend fan
        "fail_reason": "0", // ??? This is potentially documented on their wiki but I've never actually seen it last more than a few seconds with any status.
        "fan_gear": 0, // ???
        "force_upgrade": false, // ???
        "gcode_file": "/data/Metadata/plate_1.gcode", // Default name, even if it runs a different file this is the gcode_file. This is essentially useless and should look at the "sub_task" instead.
        "gcode_file_prepare_percent": "0", // Print Prep % - with how quick it is, this lasts only a few seconds. Essentially useless to monitor
        "gcode_start_time": "1673459423", // Start timestamp
        "gcode_state": "FINISH", // IDLE / RUNNING / FINISH / FAILED / PAUSE are all the ones I've seen/mapped
        "heatbreak_fan_speed": "15", // Hotend fan for the heatbreak.
        "hms": [ // HMS Status codes - wiki/slicer has more info on them but honestly feel like it isn't fully implemented yet.
            {
                "attr": 50336000,
                "code": 131074
            },
            {
                "attr": 50335744,
                "code": 131074
            },
            {
                "attr": 201327360,
                "code": 196616
            }
        ],
        "home_flag": 328, // ??? - Assuming the flag if the printer has been homed or not. Mine is 256 when I just turn on the printer. Not sure.
        "hw_switch_state": 0, // ??? - Thought it was the power on/off button, but that did not change it.
        "ipcam": {
            "ipcam_dev": "1", // ??
            "ipcam_record": "enable", // If recording of full video is enabled (not timelapse)
            "resolution": "1080p", // Camera resolution - 720p, 1080p.
            "timelapse": "disable" // Timelapse Enabled
        },
        "lifecycle": "product", // ??? - Probably left over from R&D, to identify if it's a testing unit or if it's made it off the shelf into product lifecycle.
        "lights_report": [ // Light Statuses
            {
                "mode": "on", // ON/OFF, toggleable
                "node": "chamber_light"
            },
            {
                "mode": "flashing", 
                "node": "work_light"
            }
        ],
        "mc_percent": 100, // Print progress percentage - includes progress from calibration and other steps
        "mc_print_error_code": "0",  // ?? - print specific error codes
        "mc_print_stage": "1", // ?? - print specific stage id's, not sure if any relation to action id's
        "mc_print_sub_stage": 0, // ?? - same thought as above?
        "mc_remaining_time": 0, // Print time remaining in minutes - is altered when speed profile changes :)
        "mess_production_state": "active", // ???
        "nozzle_target_temper": 150.0, // Target Nozzle Temp
        "nozzle_temper": 143.0, // Current Nozzle Temp
        "online": {
            "ahb": false, // ???
            "rfid": false // ???
        },
        "print_error": 0, // Error status codes, no mapping to them yet mostly because it sometimes clears
        "print_gcode_action": 255, // ???
        "print_real_action": 0, // ???
        "print_type": "cloud", // Assuming Cloud & LAN. SD is not a value. This only changes if you go into lan only mode as printing via sd card still has type cloud in lan mode off.
        "profile_id": "1143024", // Profile id from 3mf file for printjob
        "project_id": "1143026", // Project id from 3mf file for printjob
        "sdcard": true, // Is there an SD Card inserted
        "sequence_id": "2021", // The sequence ID of this status message
        "spd_lvl": 2, // 1/Silent, 2/Standard, 3/Sport, 4/Ludicrous
        "spd_mag": 100, // 50/Silent, 100/Standard, 124/Sport, 166%/Ludicrous
        "stg": [ // Previous stages of the printer, see Screenshot for mapping
            2,
            14,
            1
        ],
        "stg_cur": -1, // Current stage of printer, see Screenshot for mapping
        "subtask_id": "2200283", // ID of the printjob defined by 3mf file
        "subtask_name": "Canister_plate_1", // Model/3mf/job name. Closest you get to real gcode - I use this to fetch the print preview image from a FTP file download for example.
        "task_id": "2200282", // Print task id.
        "upgrade_state": { // ??? - I assume if there's a new version of firmware detected for download, these get filled.
            "ahb_new_version_number": "", 
            "ams_new_version_number": "",
            "consistency_request": false,
            "dis_state": 0,
            "err_code": 0,
            "force_upgrade": false,
            "message": "",
            "module": "null",
            "new_version_state": 2,
            "ota_new_version_number": "",
            "progress": "0",
            "sequence_id": 0,
            "status": "IDLE"
        },
        "upload": { // Progress when uploading a file to the printer, happens very fast then rests so not totally useful.
            "file_size": 0,
            "finish_size": 0,
            "message": "Good",
            "oss_url": "",
            "progress": 0,
            "sequence_id": "0903",
            "speed": 0,
            "status": "idle",
            "task_id": "",
            "time_remaining": 0,
            "trouble_id": ""
        },
        "wifi_signal": "-37dBm", // Wifi Strength
        "xcam": { 
            "allow_skip_parts": false, // ??? - I think this is an upcoming feature to skip failed parts in a multi-part print that some other slicers have, but bambu doesn't yet, judging by name.
            "buildplate_marker_detector": true, // Scans the Barcodes on the plates for assurance
            "first_layer_inspector": true, // As name
            "halt_print_sensitivity": "medium", // AI Sensititivty
            "print_halt": true, // Pause on error
            "printing_monitor": true, // AI monitoring
            "spaghetti_detector": true // Spaghetti section on
        },
        "xcam_status": "0" // ??? - Assumed this was lidar but didn't change so not sure.
```