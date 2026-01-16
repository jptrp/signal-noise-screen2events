# Screen-to-Events for WebDriver Developers

If you've spent years building test automation with Selenium, WebdriverIO, Playwright, or Cypress, Screen-to-Events will feel like a perspective shift. This guide explains the difference.

## The Core Question

**WebDriver asks:** "What state does the application *claim* to be in?"

**Screen-to-Events asks:** "What state does the user *actually see* on screen?"

```javascript
// WebDriver: Ask the app
const button = driver.findElement(By.id("play-button"));
const isDisplayed = button.isDisplayed();  // ✅ Button element exists & visible in DOM
```

```python
# Screen-to-Events: Watch the camera
frame = video_capture.read()
state = classify_state(extract_signals(frame))  # ✅ Did pixels actually change?
```

## How It Works (3 Steps)

### 1. **Capture Raw Video Frames**
Record video of what the user sees—10-30 frames per second, depending on your config.
- No application knowledge needed
- Works on any platform: web, mobile, connected TV, streaming device
- Just pixel data: `(height, width, 3)` BGR arrays from OpenCV

### 2. **Extract Signals from Each Frame**

#### Signal A: Motion Detection
```python
def motion_score(prev_frame, curr_frame):
    """Measure pixel-by-pixel changes (normalized 0-1)."""
    import cv2
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(prev_gray, curr_gray)
    return float(diff.mean() / 255.0)  # 0=frozen, 1=completely different
```

**What this tells you:**
- `motion > 0.03` → Video is playing (pixels changing)
- `motion < 0.01` → Video is paused (almost no change)

#### Signal B: Optical Character Recognition (OCR)
```python
import pytesseract
ocr_text = pytesseract.image_to_string(frame)
```

**What this tells you:**
- `"Error"` or `"Try Again"` in text → ERROR state
- `"Loading..."` or `"Buffering"` in text → BUFFERING state
- `"Skip Ad"` in text → AD state

#### Signal C: Other Heuristics (Optional)
- Color histograms (detect black screens, fade-to-black transitions)
- Template matching (detect specific UI elements)
- Edge detection (detect on-screen activity)

### 3. **Classify UX State from Signals**

```python
def classify_state(signals: Dict[str, object]) -> UXState:
    """Infer what the user is seeing based on visual signals."""
    
    ocr = (signals.get("ocr_text") or "").lower()
    motion = float(signals.get("motion") or 0.0)
    
    # Explicit error cues
    if "error" in ocr or "try again" in ocr:
        return UXState.ERROR
    
    # Explicit buffering cues
    if "loading" in ocr or "buffer" in ocr:
        return UXState.BUFFERING
    
    # Ad cues
    if "skip" in ocr and "ad" in ocr:
        return UXState.AD
    
    # Motion-based inference
    if motion >= 0.03:
        return UXState.PLAYBACK
    if motion <= 0.01:
        return UXState.PAUSED
    
    return UXState.UNKNOWN
```

**Output:** `Observation` (a Pydantic model)
```python
@dataclass
class Observation:
    t_video_ms: int              # Timestamp in video timeline
    state: UXState               # PLAYBACK, PAUSED, BUFFERING, ERROR, etc.
    confidence: float            # 0-1 (how certain we are)
    signals: Dict[str, object]   # Raw motion, OCR, etc. for debugging
```

## Why This Matters: WebDriver vs. Screen-to-Events

### Example: Validating "Playback Started"

**WebDriver test:**
```javascript
// ❌ This passes even if the video is frozen
await driver.wait(() => {
    return driver.executeScript("return window.playbackStarted === true");
}, 5000);

assert.isTrue(true);  // Event fired—test passes
```

**Problem:** The app can lie. It fires `playbackStarted`, but the video doesn't actually start playing because:
- Network latency (frame hasn't arrived yet)
- Browser bug (video element hung)
- Streaming stall (buffering but claiming to play)
- Rendering issue (codec unsupported)

**Screen-to-Events validation:**
```python
# ✅ Confirms pixels are ACTUALLY changing
observation_at_5000ms = Observation(
    t_video_ms=5000,
    state=UXState.PLAYBACK,      # Motion detected
    motion=0.15,                  # ~15% of pixels changed
    confidence=0.95
)

event_at_5010ms = NormalizedEvent(
    t_event_ms=5010,
    kind="playback_start"
)

# ✅ MATCH: App said "start" → screen shows motion 10ms later (reasonable latency)
# ❌ MISMATCH: App said "start" → screen still shows motion=0.00 (frozen, telemetry lying)
```

### Real-World Scenarios Where Screen-to-Events Catches Bugs

| Scenario | WebDriver Result | Screen-to-Events Result |
|----------|------------------|------------------------|
| App fires "playback_start" but video is frozen | ✅ Test passes | ❌ Finding: "State mismatch—app claims playback but motion=0" |
| Network latency causes 2-sec delay before first frame renders | ✅ Test passes immediately | ⏱️ Observes BUFFERING state → PLAYBACK transition, captures actual UX latency |
| Streaming service stalls (says "playing" but buffering internally) | ✅ Test passes | ❌ Finding: "Telemetry claims playback but motion=0 for 5+ seconds" |
| Ad skip button appears but doesn't render (DOM exists, CSS hidden) | ✅ Test tries to click it, fails mysteriously | ❌ Finding: "UI element not visible to user" |
| Roku remote button doesn't work (IR command sent, app ignores it) | ⚠️ Test succeeds at sending IR, can't validate result | ✅ Finding: "Remote command triggered no state change for 3 seconds" |

## Key Difference: Perspective

### WebDriver Mindset
> "I trust the application. If it says it did something, it did."

### Screen-to-Events Mindset
> "I trust the camera. If the user's screen didn't change, the application is lying."

This is especially powerful for:
- **Connected devices** (Roku, Apple TV, Fire Stick) where you can't inspect the DOM
- **Streaming platforms** (Netflix, Hulu, Disney+) where latency and buffering matter
- **Telemetry validation** (catching when analytics events don't match reality)
- **AI/ML systems** (visual confidence scores tell you when the model is uncertain)

## How Screen-to-Events Differs in Key Areas

### 1. **State Detection**

| WebDriver | Screen-to-Events |
|-----------|------------------|
| Looks for DOM elements, CSS classes, JS variables | Analyzes pixel changes and text on screen |
| Can be fooled by rendering delays | Captures the truth of what the user sees |
| Requires application knowledge | Works on any app, any platform |

### 2. **Latency Measurement**

| WebDriver | Screen-to-Events |
|-----------|------------------|
| Measures API response time | Measures end-to-end latency (API + rendering + compositing) |
| Doesn't capture render stalls | Detects when pixels are slow to update |
| Can't measure time to first frame | Knows exactly when content appears on screen |

### 3. **Telemetry Validation**

| WebDriver | Screen-to-Events |
|-----------|------------------|
| Tests the test (verifies automation works) | Validates the product (is reality matching claims?) |
| No ground truth to compare against | Screen is ground truth for correlation |
| Can't catch "telemetry lying" bugs | **Detects when events don't match observations** |

### 4. **Remote Control Verification**

| WebDriver | Screen-to-Events |
|-----------|------------------|
| Can't test Roku/Apple TV (no WebDriver) | Sends IR command, watches screen to confirm it worked |
| Relies on app APIs | Verifies UI actually changed in response |
| Limited to platforms with WebDriver | Works on any screen with a camera |

## Data Models: What You Get

### Input: `Observation` (from video)
```python
class Observation(BaseModel):
    t_video_ms: int              # Timestamp in video timeline
    state: UXState               # PLAYBACK, PAUSED, BUFFERING, ERROR, UNKNOWN
    confidence: float            # 0-1, how sure are we?
    signals: Dict[str, object]   # {"motion": 0.15, "ocr_text": "Loading...", ...}
```

### Input: `NormalizedEvent` (from telemetry)
```python
class NormalizedEvent(BaseModel):
    t_event_ms: int                  # Timestamp in telemetry/event timeline
    kind: str                        # "playback_start", "session_begin", "error", etc.
    session_key: Optional[str]       # Session ID from telemetry
    device_key: Optional[str]        # Device ID from telemetry
    metadata: Dict[str, object]      # Vendor-specific fields
    raw: Dict[str, object]           # Full original event for debugging
```

### Output: `Finding` (anomalies)
```python
class Finding(BaseModel):
    severity: Literal["INFO", "WARN", "ERROR"]
    title: str                       # "Event fired but state never observed", etc.
    description: str                 # Detailed explanation
    observation_key: Optional[int]   # Index in observations timeline
    event_key: Optional[int]         # Index in events timeline
    evidence: Optional[List[str]]    # Paths to evidence frames (screenshots)
```

## How It Fits Your Testing Strategy

### You Still Need WebDriver For:
- ✅ Functional UI testing (form validation, navigation)
- ✅ Interaction testing (clicks, scrolls, keyboard)
- ✅ A/B test verification (feature flags, experiments)
- ✅ API contract testing (schema, response codes)

### Screen-to-Events Adds:
- ✅ **Visual validation** (what the user actually sees)
- ✅ **Latency analysis** (end-to-end timing)
- ✅ **Telemetry audit** (catching when claims don't match reality)
- ✅ **Remote device testing** (no WebDriver needed)
- ✅ **Evidence collection** (screenshots of problems for debugging)

### In Practice
```
WebDriver Test Suite
     ↓
  (app interacts correctly)
     ↓
Screen-to-Events Session
     ↓
  (was what the user saw correct?)
     ↓
Telemetry Correlation
     ↓
  (did analytics match reality?)
```

## Getting Started

If you're comfortable with:
- Python ≥3.10
- Pydantic models
- Environment setup (`pip install -e ".[video]"`)

Then you already understand the hard part. The video analysis is just:

```python
from screen2events.video.motion import MotionTracker
from screen2events.video.detectors import classify_state

tracker = MotionTracker()

for frame in video_stream:
    motion = tracker.update(frame)
    if motion is not None:
        signals = {"motion": motion}
        state = classify_state(signals)
        print(f"Observed: {state} (motion={motion:.2f})")
```

See [README.md](../README.md) and [examples/](../examples/) to run a full session.

## FAQ

**Q: Do I need a camera pointed at my TV?**  
A: Yes, for now. Future work could use streaming APIs (HDMI capture cards, remote frame buffers). But hardware video capture is cheap and reliable.

**Q: Won't OCR be slow?**  
A: Yes, very. It's optional—only enable it if you need to detect text ("Error", "Loading"). Disable it for streaming platforms where motion is sufficient. Default: off.

**Q: What if the screen is mostly static (loading screen)?**  
A: That's the point! Motion is low → `BUFFERING` state. Traditional tests miss this; they just wait for a DOM element that might never render.

**Q: Can I use this with WebDriver?**  
A: Yes! Run a WebDriver test *and* record video in parallel. Correlate events from both. Get the best of both worlds.

**Q: How accurate is motion detection?**  
A: ~90% for clear video (good lighting, stable camera). OCR is lower (~70%) depending on font/resolution. Confidence scores tell you when to trust an observation.

---

**For more details:** See [.github/copilot-instructions.md](../.github/copilot-instructions.md) for the full architecture.
