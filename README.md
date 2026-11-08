# Stage 1 — Ignite: Power On Your AI Robot's Brain

Board bring-up, a camera sensor, and a first on-device AI task on **D-Robotics RDK X5**.

| Challenge | Result | Evidence |
| --- | --- | --- |
| 1. Board bring-up | Flash ✅ · Network ✅ · SSH ✅ · Community ✅ | [Screenshot A](images/A_flash_ssh.png) |
| 2. Sensor explorer | Camera — Orbbec Astra Pro HD over USB | [Screenshot B](images/B_camera.png) |
| 3. First AI task | YOLO object detection on BPU, live camera | [Screenshot C](images/C_yolo.png) |

---

## Environment

| Item | Version / value |
| --- | --- |
| Board | RDK X5 |
| OS image | `rdk-x5-ubuntu22-preinstalled-desktop-3.5.0-arm64.img.xz` |
| Base OS | Ubuntu 22.04 (RDK OS 3.5.0) |
| Python | 3.10 (pre-installed) |
| OpenCV | pre-installed `cv2` |
| BPU runtime | BPU Platform 1.3.6 · DNN runtime 1.24.5 (HBRT 3.15.55) |
| Host tool | RDK Studio (Windows 11) |

### Dependencies

Everything below ships with the RDK OS 3.5.0 desktop image, except `v4l-utils`:

```bash
apt update
apt install -y v4l-utils
```

---

## Challenge 1 — Board bring-up

### 1.1 Flash the system image

1. RDK Studio → **Device & development** (wrench icon) → **Build and delivery** → **Flasher**.
2. Device: **RDK X5 / X5 Module**.
3. Image: **Local image** → `rdk-x5-ubuntu22-preinstalled-desktop-3.5.0-arm64.img.xz` (from `archive.d-robotics.cc/downloads/os_images/rdk_x5/`).
4. Target drive: 64 GB microSD via USB card reader.
5. Flash mode: **Stable mode** → **Start flashing** → **Erase and flash**.
6. Stages: Download (skipped, local file) → Decompress → Write → Verify → **Done**.
7. Insert the card into the board (power off), connect HDMI, power with 5V/5A. The Ubuntu desktop appears after ~45 s.

### 1.2 Connect RDK Studio over USB Type-C

1. Connect the board's **QuickLink** Type-C port to the PC (the board must already be booted).
2. RDK Studio → **Connect device** → **RDK Type-C direct**.
3. Press **Refresh**, then pick the network adapter that appears after plugging the cable in.
4. **Start connection** → board reachable at `192.168.128.10`.

### 1.3 Network (Wi-Fi + internet)

```bash
nmcli device wifi rescan
nmcli device wifi list
wifi_connect "<SSID>" "<PASSWORD>"    # credentials redacted
ping -c 3 google.com
curl -I https://www.google.com
```

### 1.4 SSH from the PC

From Windows PowerShell:

```powershell
ssh root@192.168.128.10
```

On the board:

```bash
uname -a
htop
```

### 1.5 Community

Stage 1 check-in posted in my personal Discord thread: `<paste permalink here>`

---

## Challenge 2 — Sensor explorer (Camera)

| Item | Value |
| --- | --- |
| Category | Camera |
| Device | Orbbec Astra Pro HD (RGB stream) |
| Interface | **USB (UVC)** → `/dev/video0` (`/dev/video1` = metadata node) |
| Format used | MJPG 1280×720 |
| Verified with | `v4l2-ctl`, OpenCV `cv2.VideoCapture` (V4L2 backend) |

All evidence is written to one folder on the board:

```bash
mkdir -p /root/evidence && cd /root/evidence
v4l2-ctl --list-devices | tee sensor_log.txt
python3 scripts/capture_astra.py /root/evidence/camera_test.jpg | tee -a sensor_log.txt
```

[`evidence/sensor_log.txt`](evidence/sensor_log.txt):

```
Astra Pro HD Camera: Astra Pro  (usb-xhci-hcd.2.auto-1.2.1):
	/dev/video0
	/dev/video1
	/dev/media0

capture ok: True size: (720, 1280, 3)
```

Captured frame: [`evidence/camera_test.jpg`](evidence/camera_test.jpg)

---

## Challenge 3 — First AI task (YOLO object detection)

| Item | Value |
| --- | --- |
| Task | YOLO object detection (COCO, 80 classes) |
| Model | `yolov5s_v2_672x672_bayese_nv12` (672×672, NV12 input) |
| Accelerator | RDK X5 BPU (`bpu_cores: [0]`) |
| Runtime | BPU Platform 1.3.6 · DNN runtime 1.24.5 (HBRT 3.15.55) |
| Input | Live Orbbec Astra Pro HD feed, `/dev/video0` |
| Source | Official RDK OS demo `/app/pydev_demo/07_usb_camera_sample/usb_camera_yolov5x.py` |

### Headless run over SSH

The official demo opens a full-screen OpenCV window, which fails over SSH
(`qt.qpa.xcb: could not connect to display`). I made a copy that writes the
annotated frame to a file instead of showing a window:

```bash
cd /app/pydev_demo/07_usb_camera_sample
cp usb_camera_yolov5x.py /root/evidence/yolo_headless.py
sed -i -E \
 -e "s#cv2\.imshow\(([^,]+),[[:space:]]*(.+)\)[[:space:]]*\$#cv2.imwrite('/root/evidence/yolo_result.jpg', \2)#" \
 -e "s/cv2\.waitKey\(/(lambda *a: -1)(/g" \
 -e "s/cv2\.(namedWindow|setWindowProperty|resizeWindow|moveWindow|destroyAllWindows)\(/(lambda *a, **k: None)(/g" \
 /root/evidence/yolo_headless.py
```

| Original line | Headless copy |
| --- | --- |
| `cv2.imshow("YOLOv5X Detection", vis)` | `cv2.imwrite('/root/evidence/yolo_result.jpg', vis)` |
| `cv2.namedWindow` / `setWindowProperty` / `destroyAllWindows` | no-op |
| `cv2.waitKey(1)` | returns `-1`, loop continues |

Run for 20 seconds from the demo folder (so relative model/label paths resolve).
`-u` keeps Python output unbuffered so the log is complete when `timeout` stops it:

```bash
cd /app/pydev_demo/07_usb_camera_sample
timeout 20 python3 -u /root/evidence/yolo_headless.py 2>&1 | tee /root/evidence/yolo_log.txt
```

### Result

[`evidence/yolo_log.txt`](evidence/yolo_log.txt) (excerpt):

```
Opening video device: /dev/video0
Open USB camera successfully
[BPU_PLAT]BPU Platform Version(1.3.6)! soc info(x5)
[DNN] Runtime version = 1.24.5_(3.15.55 HBRT)
=== Model Name List ===
['yolov5s_v2_672x672_bayese_nv12']
  bpu_cores   : [0]
```

Annotated output [`evidence/yolo_result.jpg`](evidence/yolo_result.jpg): `person 0.41` detected on the live camera frame.

### File transfer (scp)

All evidence was copied from the board to the PC in one command:

```powershell
scp -r root@192.168.128.10:/root/evidence .
```

---

## Troubleshooting

| Problem | Cause | Fix |
| --- | --- | --- |
| Can't find where to flash in RDK Studio | The first-run wizard was skipped | Wrench icon → scroll to **Build and delivery** → **Flasher** |
| **Start flashing** button not visible | Window too short for the page | Maximize the window or zoom out with `Ctrl` + `-` |
| `No removable SD/eMMC targets detected` | Card reader lost or no permission | Re-plug, **Refresh drives**, run RDK Studio as administrator |
| Decompress step is slow, % barely moves | No system `xz`, RDK Studio falls back to a WASM decompressor | Wait (took ~7 min), or extract the `.img` with 7-Zip first |
| **Connect device** times out | SD card still in the PC, so the board is not running | Insert the card and boot the board first |
| Wrong adapter in the Type-C NIC list | `192.168.56.1` is the VirtualBox host-only adapter | Re-plug the cable, **Refresh**, pick the newly added adapter |
| PowerShell SSH: `Permission denied` | Wrong password (input is hidden while typing) | Retype carefully; the `sunrise` account also works |
| YOLO demo: `qt.qpa.xcb: could not connect to display` | Demo opens a window but SSH has no display | Use the headless copy (`imshow` → `imwrite`) or run from Remote desktop |
| `yolo_log.txt` missing lines after `timeout` | Python buffers output when piped | Run with `python3 -u` |
| RDK Studio: `Another device connection is using the same board IP` | Old device entry still saved | Delete the old device and clear history, then reconnect |
| RDK Studio: `Could not read the complete host network state` | No permission to change host network | Run RDK Studio as administrator |

## References

- [RDK X5 documentation](https://developer.d-robotics.cc/rdk_x_doc/en/RDK)
- [RDK Studio](https://developer.d-robotics.cc/en/rdkstudio)
- [RDK Model Zoo](https://github.com/D-Robotics/rdk_model_zoo)
- [RDK course demos](https://github.com/D-Robotics/rdk-course-demos)
