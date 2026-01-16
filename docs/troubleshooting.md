# Troubleshooting Guide

Common issues and solutions when running Screen-to-Events.

## Installation & Setup

### Issue: `ImportError: No module named 'cv2'`

**Cause:** OpenCV not installed (required for motion detection)

**Solution:**
```bash
pip install -e '.[video]'  # Installs opencv-python
```

Or install manually:
```bash
pip install opencv-python
```

---

### Issue: `ModuleNotFoundError: No module named 'pytesseract'`

**Cause:** pytesseract installed but system Tesseract not found

**Solution:**

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

Then verify:
```bash
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

---

### Issue: `FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'`

**Cause:** FFmpeg not installed (optional, used for video capture)

**Solution:**

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu:**
```bash
sudo apt-get install ffmpeg
```

---

## Video Capture Issues

### Issue: No frames captured from HDMI device

**Cause:** Device not connected, wrong index, or permissions issue

**Solution:**

1. **Check device is connected:**
   ```bash
   # List USB devices
   system_profiler SPUSBDataType | grep -i "capture\|video"
   ```

2. **Find correct device index:**
   ```python
   import cv2
   
   for i in range(10):
       cap = cv2.VideoCapture(i)
       if cap.isOpened():
           print(f"Device {i}: available")
           ret, frame = cap.read()
           if ret:
               print(f"  Resolution: {frame.shape}")
           cap.release()
   ```

3. **Check permissions (Linux):**
   ```bash
   sudo usermod -a -G video $USER
   # Then log out and back in
   ```

---

### Issue: Low frame rate or frozen frames

**Cause:** USB bandwidth, slow disk, or capture device overload

**Solution:**

1. **Reduce resolution in config:**
   ```yaml
   video:
     width: 1280      # Instead of 1920
     height: 720      # Instead of 1080
     fps: 10          # Instead of 30
   ```

2. **Use faster disk (SSD instead of HDD)**

3. **Reduce other USB device load** (disconnect peripherals)

---

## Motion Detection Issues

### Issue: Motion detection too sensitive (noisy signal)

**Problem:** Threshold set too low; detects compression artifacts, noise, shadows

**Solution:**

1. **Increase motion threshold in config:**
   ```yaml
   video:
     motion:
       playback_motion_min: 0.05  # Was 0.03
       paused_motion_max: 0.005   # Was 0.01
   ```

2. **Disable motion for static content:**
   ```python
   # Use layout/OCR instead of motion for pages like:
   # - Home screen (static menu)
   # - Settings (form fields)
   # - Search results (text-heavy)
   ```

3. **Lower video quality:**
   - Compression artifacts inflate motion scores
   - Use lower bitrate capture (paradoxically helps)

---

### Issue: Motion detection too insensitive (missing real motion)

**Problem:** Threshold set too high; misses subtle motion

**Solution:**

1. **Decrease motion threshold:**
   ```yaml
   video:
     motion:
       playback_motion_min: 0.02  # Was 0.03
       paused_motion_max: 0.005
   ```

2. **Check video quality:**
   - Blurry or low-res video → less detectable motion
   - Ensure HDMI capture is at native resolution

3. **Verify lighting:**
   - Dark scenes reduce motion detection
   - Increase brightness/contrast if possible

4. **Increase sample rate:**
   ```yaml
   video:
     sample_fps: 20  # More frequent checks
   ```

---

## OCR & Page Detection Issues

### Issue: OCR failing to detect text ("home", "settings", etc.)

**Problem:** Text too small, low resolution, unusual font, or language

**Solution:**

1. **Check resolution:**
   - Tesseract works best at ≥300 DPI
   - If HDMI capture is low-res, upscale before OCR:
   ```python
   upscaled = cv2.resize(frame, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
   ocr_text = pytesseract.image_to_string(upscaled)
   ```

2. **Disable OCR, focus on motion/layout:**
   ```yaml
   video:
     enable_ocr: false
   ```
   Use motion patterns and layout detection instead.

3. **Region-specific OCR only:**
   ```python
   # Instead of full frame, OCR just the navigation bar
   top_nav = frame[0:80, :]
   ocr_text = pytesseract.image_to_string(top_nav)
   ```

4. **Increase OCR confidence threshold:**
   ```python
   # Only trust OCR if very confident
   if page_confidence > 0.8:  # Was 0.6
       return page
   else:
       fallback_to_layout_detection()
   ```

5. **Check Tesseract version:**
   ```bash
   tesseract --version
   # v5.0+ is significantly better than v4
   ```

---

### Issue: Page detection confused (think "home" is "search")

**Problem:** OCR keywords overlap or are ambiguous

**Solution:**

1. **Add device-specific signatures:**
   ```python
   # Instead of generic keywords, use platform-specific ones
   ROKU_KEYWORDS = {
       "home": ["home hub", "my channels"],  # More specific
       "search": ["search", "find", "browse"],
   }
   ```

2. **Require multiple keyword matches:**
   ```python
   matches = [kw in ocr_text for kw in keywords]
   if sum(matches) >= 2:  # At least 2 keywords must match
       return page
   ```

3. **Combine with layout detection:**
   ```python
   # If OCR says "home" but layout shows scrolling, trust layout
   if ocr_page == "home" and motion > 0.08:
       return "browse"  # Override
   ```

---

## Alignment & Correlation Issues

### Issue: Alignment fails (offset/drift calculation)

**Problem:** Not enough anchor events, or clock skew too large

**Solution:**

1. **Provide explicit anchor point in config:**
   ```yaml
   alignment:
     app_open_video_ms: 5000  # Manually specify instead of auto-detect
   ```

2. **Use multiple anchor events:**
   - Don't rely on single "session_start" event
   - Use "playback_start", "buffer_end", "pause" as cross-checks
   - More anchors = more robust alignment

3. **Check clock synchronization:**
   - If video clock and event clock are wildly different
   - Manually measure offset:
   ```python
   # At 5-second mark in video, what event timestamp?
   video_time = 5000  # ms
   event_time = 5010  # ms (from telemetry)
   offset = event_time - video_time  # 10ms
   ```

4. **Accept approximate alignment for initial runs:**
   ```python
   # Use a wider correlation window if drift is unclear
   match_window_ms = 5000  # 5 seconds (was 1000ms)
   ```

---

### Issue: Findings report shows many false positives

**Problem:** Correlation threshold too strict

**Solution:**

1. **Increase match tolerance:**
   ```yaml
   correlate:
     match_window_ms: 2000  # Was 1000ms
     confidence_threshold: 0.5  # Was 0.7
   ```

2. **Prioritize high-confidence observations:**
   ```python
   # Only match if observation has high confidence
   if observation.confidence > 0.8:
       match(observation, event)
   ```

3. **Filter noisy telemetry:**
   - Discard events with confidence < 0.5
   - Ignore heartbeat events (not meaningful for correlation)

---

## Remote Control (IR) Issues

### Issue: IR commands not working on device

**Problem:** Device not receiving signal, wrong protocol, or network issue

**Solution:**

1. **Check IR blaster connectivity:**
   - Power indicator on blaster?
   - USB cable connected securely?
   - Correct device port?

2. **Verify device is on:**
   ```bash
   # Test with simple command
   curl -X POST http://<roku_ip>:8060/keypress/Home
   ```

3. **Check network connectivity:**
   ```bash
   ping <roku_ip>
   ```

4. **Use correct IR protocol:**
   - **Roku:** Broadlink/Orvibo standard
   - **Apple TV:** HomeKit or custom HTTP
   - See [docs/IR_BLASTER.md](IR_BLASTER.md) for device-specific setup

5. **Enable logging to debug:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   # Watch for IR command output
   ```

---

### Issue: IR command executed but screen didn't respond

**Problem:** Command reached device but had no effect

**Solution:**

1. **Verify screen response with vision:**
   ```python
   # Send IR command
   send_ir("play")
   
   # Check if screen actually changed
   time.sleep(0.5)
   motion = measure_motion(frame_before, frame_after)
   
   if motion < 0.02:
       raise Finding("IR command not verified—no visual response")
   ```

2. **Check device state before command:**
   - Can't press "play" on a device already playing
   - Can't pause a paused device
   - Validate state machine first

3. **Increase inter-command delay:**
   ```yaml
   control:
     ir_command_delay_ms: 500  # Was 100ms
   ```

4. **Check for on-screen overlays:**
   - Dialog box blocking navigation?
   - Use page detection to wait for dismissal

---

## Telemetry Integration Issues

### Issue: No events found in S3/Athena/OpenSearch

**Problem:** Wrong bucket, prefix, time range, or credentials

**Solution:**

1. **Verify S3 credentials:**
   ```bash
   aws s3 ls s3://your-bucket/your-prefix/
   ```

2. **Check time range:**
   ```yaml
   telemetry:
     time_range_start_ms: 4000  # Before app open
     time_range_end_ms: 300000   # After session ends
   ```

3. **Verify event format:**
   - Is JSONL properly formatted? (one JSON object per line)
   - Are timestamps in milliseconds?
   - Do events have required fields (`t_event_ms`, `kind`)?

4. **Check permissions:**
   - AWS IAM role has `s3:GetObject`
   - Athena role has query permissions
   - OpenSearch user has read access

---

### Issue: Events not correlating with observations

**Problem:** Time alignment off, or event kinds don't match observation states

**Solution:**

1. **Verify time alignment:**
   ```python
   # Print a few observations and events side-by-side
   for obs in observations[:5]:
       print(f"Video t={obs.t_video_ms}, state={obs.state}")
   
   for evt in events[:5]:
       print(f"Event t={evt.t_event_ms}, kind={evt.kind}")
   ```

2. **Update `kind_to_state` mapping:**
   ```python
   # In correlate/match.py
   KIND_TO_STATE = {
       "playback_start": UXState.PLAYBACK,
       "pause": UXState.PAUSED,
       "buffer_start": UXState.BUFFERING,
       # Add your custom event kinds here
   }
   ```

3. **Increase match window:**
   ```yaml
   correlate:
     match_window_ms: 3000  # Give more slack for latency
   ```

---

## Performance Issues

### Issue: OCR taking too long (>1 sec per frame)

**Solution:**

1. **Sample OCR less frequently:**
   ```python
   detector = OptimizedPageDetector(ocr_sample_rate=10)  # Every 1 second at 10fps
   ```

2. **Use region-based OCR:**
   ```python
   # OCR just nav bar, not full frame
   nav = frame[0:80, :]
   ocr_text = pytesseract.image_to_string(nav)
   ```

3. **Downscale before OCR:**
   ```python
   small = cv2.resize(frame, (360, 240))
   ocr_text = pytesseract.image_to_string(small)
   ```

4. **Disable OCR for simple cases:**
   ```yaml
   video:
     enable_ocr: false  # Use motion + layout only
   ```

---

### Issue: Full pipeline taking hours for short video

**Problem:** Unoptimized or missing optimization flags

**Solution:**

1. **Check frame sampling rate:**
   ```yaml
   video:
     sample_fps: 5  # Lower = faster, less detail
   ```

2. **Disable unnecessary processing:**
   ```yaml
   control:
     enable_ir_verification: false  # If not using IR
   
   video:
     enable_ocr: false  # If not needed
   ```

3. **Run with limited frames for testing:**
   ```bash
   s2e run --config config.yaml --video session.mp4 --max-frames 100
   ```

---

## Debugging Tips

### Enable verbose logging:

```bash
export SCREEN2EVENTS_DEBUG=1
s2e run --config config.yaml --video session.mp4
```

### Inspect intermediate outputs:

```bash
# After a run, examine
cat runs/<timestamp>/observations.jsonl | head -20
cat runs/<timestamp>/events.jsonl | head -20
cat runs/<timestamp>/findings.jsonl | head -20
```

### Manual frame inspection:

```python
import cv2

cap = cv2.VideoCapture("session.mp4")
frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    if frame_count % 10 == 0:  # Every 10 frames
        cv2.imwrite(f"frames/frame_{frame_count:05d}.png", frame)
    
    frame_count += 1

# Then examine specific frames
```

### Test OCR on a single frame:

```python
import cv2
import pytesseract

frame = cv2.imread("frames/frame_00050.png")
text = pytesseract.image_to_string(frame)
print(text)
```

---

## Still Stuck?

1. **Check existing issues:** https://github.com/jptrp/signal-noise-screen2events/issues
2. **Review logs:** Look for stack traces in terminal output
3. **Test with demo data:** Run `examples/validate_demo.py` to verify base setup
4. **Open an issue** with:
   - Exact error message
   - Your config file (redact credentials)
   - Sample frame or video excerpt
   - Python/OS version
