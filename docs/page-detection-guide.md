# Page Detection Guide: Recognizing Streaming App Navigation

This guide covers techniques for detecting **which page the user is viewing** in a streaming application: home, live TV, guide, settings, search, catalog browsing, playback, etc.

This is different from **state detection** (playback vs. buffering vs. error). Page detection is about **navigation context**—where in the app are they?

## Overview: Three Core Strategies

| Strategy | Speed | Accuracy | Reliability | Best For |
|----------|-------|----------|-------------|----------|
| **OCR (Text Recognition)** | Slow (~500ms) | High (~90%) | High (text is explicit) | Primary signal; label confirmation |
| **Layout Detection** | Fast (~10ms) | Medium (~70%) | Medium (fragile to UI changes) | Fallback when OCR unavailable; real-time tracking |
| **Motion Patterns** | Instant (<1ms) | Low (~60%) | Low (ambiguous across pages) | Final fallback; distinguishing playback from browse |

## Strategy 1: OCR-Based Page Detection (Most Reliable)

### Why OCR Works
Streaming apps always display navigation labels:
- Roku: "Home Hub", "My Channels", "Search", "Settings"
- Apple TV: "Up Next", "Watch Now", "Library", "Search", "Account"
- Fire TV: "Home", "Live", "Search", "Your Apps"

These labels are **invariant** across UI redesigns—if you're on the Home page, "Home" appears somewhere on screen.

### Implementation

#### Step 1: Extract OCR Text

```python
import pytesseract
import cv2
import numpy as np

def extract_ocr_signals(frame: np.ndarray) -> Dict[str, str]:
    """Extract OCR text from full frame and key regions."""
    
    full_text = pytesseract.image_to_string(frame)
    
    # Optimization: OCR is slow, so focus on navigation bars
    height, width = frame.shape[:2]
    
    # Top navigation bar (typical for streaming apps)
    top_nav = frame[0:int(height * 0.1), :]
    top_nav_text = pytesseract.image_to_string(top_nav)
    
    # Bottom navigation bar (sometimes present)
    bottom_nav = frame[int(height * 0.9):, :]
    bottom_nav_text = pytesseract.image_to_string(bottom_nav)
    
    # Center region (main content area)
    center = frame[int(height * 0.2):int(height * 0.8), int(width * 0.1):int(width * 0.9)]
    center_text = pytesseract.image_to_string(center)
    
    return {
        "full": full_text.lower(),
        "top_nav": top_nav_text.lower(),
        "bottom_nav": bottom_nav_text.lower(),
        "center": center_text.lower(),
    }
```

#### Step 2: Page Classification from Keywords

```python
class PageDetector:
    """Multi-platform page detection using OCR."""
    
    # Define signatures per platform
    SIGNATURES = {
        "roku": {
            "home": ["home hub", "home", "my channels"],
            "live_tv": ["live tv", "live channels", "on now"],
            "guide": ["guide", "what's on", "channel guide"],
            "search": ["search", "find", "browse all"],
            "settings": ["settings", "player", "about"],
            "my_stuff": ["my stuff", "subscriptions", "watch history"],
        },
        "apple_tv": {
            "home": ["up next", "watch now", "home"],
            "tv_shows": ["tv", "shows", "tv shows"],
            "movies": ["movies", "cinema", "watch movies"],
            "search": ["search", "find"],
            "library": ["library", "your library"],
            "account": ["account", "settings", "profile"],
        },
        "fire_tv": {
            "home": ["home", "your apps", "personalized"],
            "live": ["live", "live tv", "channels"],
            "search": ["search", "find"],
            "your_apps": ["your apps", "app library"],
            "settings": ["settings", "device options"],
        },
    }
    
    def __init__(self, platform: str = "roku"):
        self.platform = platform
        self.signatures = self.SIGNATURES.get(platform, self.SIGNATURES["roku"])
    
    def detect_page(self, ocr_signals: Dict[str, str]) -> Tuple[str, float]:
        """Detect page and return (page_name, confidence)."""
        
        # Prioritize top_nav (most reliable)
        for region in ["top_nav", "center", "bottom_nav", "full"]:
            text = ocr_signals[region]
            
            for page_name, keywords in self.signatures.items():
                # Match if any keyword appears in this region
                matches = [kw in text for kw in keywords]
                if any(matches):
                    # Confidence: fraction of keywords that matched
                    confidence = sum(matches) / len(keywords)
                    return page_name, confidence
        
        return "unknown", 0.0

# Usage
detector = PageDetector(platform="roku")
ocr_signals = extract_ocr_signals(frame)
page, confidence = detector.detect_page(ocr_signals)
print(f"Detected: {page} (confidence: {confidence:.2%})")
```

#### Step 3: Integrate into State Machine

```python
def classify_state_with_pages(
    signals: Dict[str, object],
    cfg: DetectorConfig,
    page_detector: PageDetector
) -> Tuple[str, str]:  # (page, activity)
    """Classify both page and activity."""
    
    frame = signals.get("frame")
    motion = float(signals.get("motion") or 0.0)
    ocr_signals = signals.get("ocr_signals")
    
    # Detect page from OCR
    page, page_confidence = page_detector.detect_page(ocr_signals)
    
    # Detect activity (playback, browsing, etc.) from motion + OCR
    if motion >= cfg.playback_motion_min:
        activity = "playback"
    elif motion <= cfg.paused_motion_max:
        activity = "paused"
    elif "loading" in ocr_signals["full"]:
        activity = "buffering"
    else:
        activity = "browsing"
    
    return page, activity
```

### Performance Optimization: Cache & Skip OCR

OCR is expensive. Run it selectively:

```python
class OptimizedPageDetector:
    """Reduce OCR calls via caching and sampling."""
    
    def __init__(self, platform: str, ocr_sample_rate: int = 5):
        self.detector = PageDetector(platform)
        self.ocr_sample_rate = ocr_sample_rate  # Run OCR every Nth frame
        self.frame_count = 0
        self.cached_page = "unknown"
        self.cached_confidence = 0.0
        self.last_motion = 0.0
    
    def update(
        self,
        frame: np.ndarray,
        motion: float
    ) -> Tuple[str, float]:
        """
        Update page detection with smart OCR sampling.
        
        OCR every Nth frame, or if motion suggests page change.
        """
        self.frame_count += 1
        self.last_motion = motion
        
        # Run OCR periodically
        if self.frame_count % self.ocr_sample_rate == 0:
            ocr_signals = extract_ocr_signals(frame)
            self.cached_page, self.cached_confidence = self.detector.detect_page(ocr_signals)
        
        # If motion drops suddenly, page might have changed—run OCR
        if motion < 0.01 and self.last_motion > 0.05:
            ocr_signals = extract_ocr_signals(frame)
            self.cached_page, self.cached_confidence = self.detector.detect_page(ocr_signals)
        
        return self.cached_page, self.cached_confidence
```

---

## Strategy 2: Layout & Template Detection (Fast)

### Why Layout Matters
Even without reading text, you can distinguish pages by **visual structure**:
- **Home screen:** Navigation menu + content grid (high entropy)
- **Playback:** Minimal UI, large video area (smooth gradients)
- **Search:** Text input field + results list (vertical stripes)
- **Settings:** Form fields, toggles, text (structured layout)

### Implementation

#### Detect Navigation Bar Structure

```python
import cv2
import numpy as np

def detect_nav_bar_buttons(frame: np.ndarray, nav_region_height: int = 80) -> int:
    """Count button-like regions in navigation bar."""
    
    # Extract top navigation bar
    nav = frame[0:nav_region_height, :]
    
    # Convert to HSV for better color-based detection
    hsv = cv2.cvtColor(nav, cv2.COLOR_BGR2HSV)
    
    # Detect bright regions (typical button appearance)
    # Most streaming apps use light text/buttons on dark backgrounds
    lower_bright = np.array([0, 0, 180])      # Low saturation, high value
    upper_bright = np.array([180, 50, 255])
    
    mask = cv2.inRange(hsv, lower_bright, upper_bright)
    
    # Find contours (button-like shapes)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter by size (remove noise)
    valid_buttons = [
        c for c in contours
        if cv2.contourArea(c) > 100  # At least 100 pixels
    ]
    
    return len(valid_buttons)

def detect_page_from_layout(frame: np.ndarray) -> str:
    """Classify page based on layout features."""
    
    button_count = detect_nav_bar_buttons(frame)
    
    height, width = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect edges (structure indicator)
    edges = cv2.Canny(gray, 100, 200)
    edge_density = np.sum(edges > 0) / edges.size
    
    # Detect text regions (search box, form fields)
    # Text has high contrast edges
    text_regions = np.sum(edges[int(height*0.1):int(height*0.3), :] > 0)
    
    # Detect motion/content area (video playback is smooth, browse is structured)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = laplacian.var()
    
    # Decision tree
    if button_count >= 4:
        return "home"  # Rich navigation = home screen
    
    if text_regions > height * width * 0.05 and edge_density > 0.15:
        return "search"  # Text input + structured results
    
    if variance < 50:  # Smooth video
        return "playback"
    
    if edge_density > 0.2:  # High structure
        return "settings"  # Settings have form fields
    
    return "browse"
```

#### Template Matching (Advanced)

If you have reference screenshots for each page:

```python
def template_match_page(
    frame: np.ndarray,
    page_templates: Dict[str, np.ndarray]
) -> Tuple[str, float]:
    """
    Match current frame against reference templates.
    
    Args:
        frame: Current video frame
        page_templates: Dict of page_name -> reference image
    
    Returns:
        (best_match_page, similarity_score)
    """
    
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    best_page = "unknown"
    best_score = 0.0
    
    for page_name, template in page_templates.items():
        gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        # Scale template to match frame resolution
        template_resized = cv2.resize(
            gray_template,
            (gray_frame.shape[1], gray_frame.shape[0])
        )
        
        # Compute correlation
        result = cv2.matchTemplate(
            gray_frame,
            template_resized,
            cv2.TM_CCOEFF
        )
        
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # Normalize score to 0-1
        score = (max_val - min_val) / (max_val - min_val + 1e-6)
        
        if score > best_score:
            best_score = score
            best_page = page_name
    
    return best_page, best_score
```

---

## Strategy 3: Motion Pattern Analysis (Fastest)

### Why Motion Matters
Different pages have characteristic motion patterns:
- **Playback:** Continuous, sustained motion (0.05–0.30)
- **Browsing:** Intermittent motion (scrolling, clicks)
- **Paused:** Near-zero motion (<0.01)
- **Loading:** Very brief motion spikes

### Implementation

```python
class MotionPatternDetector:
    """Infer page from motion history patterns."""
    
    def __init__(self, window_size: int = 30):  # ~3 seconds at 10 fps
        self.window_size = window_size
        self.motion_history = []
        self.page_history = []
    
    def update(self, motion: float) -> Tuple[str, float]:
        """Analyze motion pattern and infer page."""
        
        self.motion_history.append(motion)
        if len(self.motion_history) > self.window_size:
            self.motion_history.pop(0)
        
        if len(self.motion_history) < 5:
            return "unknown", 0.0  # Need history
        
        # Compute statistics
        recent = np.array(self.motion_history)
        mean_motion = np.mean(recent)
        max_motion = np.max(recent)
        std_motion = np.std(recent)
        
        # Decision logic
        page, confidence = self._classify_from_motion(mean_motion, max_motion, std_motion)
        
        self.page_history.append((page, confidence))
        
        return page, confidence
    
    def _classify_from_motion(
        self,
        mean: float,
        max_val: float,
        std: float
    ) -> Tuple[str, float]:
        """Classify page from motion statistics."""
        
        # Playback: high, sustained motion
        if 0.05 <= mean <= 0.25 and std < 0.08:
            return "playback", 0.8  # Moderate confidence
        
        # Browsing: variable motion (scrolling, clicking)
        if 0.01 < mean < 0.08 and std > 0.03:
            return "browse", 0.6
        
        # Paused/static page: very low motion
        if mean < 0.01 and max_val < 0.02:
            return "static_page", 0.7  # Could be home, settings, etc.
        
        # Buffering: motion spikes
        if max_val > 0.15 and std > 0.1:
            return "buffering", 0.5
        
        return "unknown", 0.0

# Usage
detector = MotionPatternDetector()

for motion in motion_stream:
    page, confidence = detector.update(motion)
    if confidence > 0.6:
        print(f"Page: {page}")
```

---

## Strategy 4: Hybrid Approach (Recommended)

Combine all strategies with a confidence-weighted fallback chain:

```python
class HybridPageDetector:
    """Multi-signal page detection with intelligent fallback."""
    
    def __init__(self, platform: str = "roku", enable_ocr: bool = True):
        self.ocr_detector = OptimizedPageDetector(platform) if enable_ocr else None
        self.layout_detector = LayoutDetector()
        self.motion_detector = MotionPatternDetector()
        
        # Weights: OCR is most reliable
        self.weights = {
            "ocr": 0.6,
            "layout": 0.25,
            "motion": 0.15,
        }
    
    def update(
        self,
        frame: np.ndarray,
        motion: float
    ) -> Tuple[str, float]:
        """Detect page with multi-signal fusion."""
        
        signals = {}
        confidences = {}
        
        # OCR signal (if enabled)
        if self.ocr_detector:
            page_ocr, conf_ocr = self.ocr_detector.update(frame, motion)
            signals["ocr"] = page_ocr
            confidences["ocr"] = conf_ocr
        
        # Layout signal
        page_layout = self.layout_detector.detect(frame)
        signals["layout"] = page_layout
        confidences["layout"] = 0.7  # Assumed confidence
        
        # Motion signal
        page_motion, conf_motion = self.motion_detector.update(motion)
        signals["motion"] = page_motion
        confidences["motion"] = conf_motion
        
        # Fusion: weighted vote
        best_page, best_confidence = self._fuse_signals(signals, confidences)
        
        return best_page, best_confidence
    
    def _fuse_signals(
        self,
        signals: Dict[str, str],
        confidences: Dict[str, float]
    ) -> Tuple[str, float]:
        """Fuse multi-signal detections."""
        
        # Weighted voting
        votes = {}
        total_weight = 0.0
        
        for source, page in signals.items():
            weight = self.weights.get(source, 0.1)
            confidence = confidences.get(source, 0.5)
            weighted_confidence = weight * confidence
            
            if page not in votes:
                votes[page] = 0.0
            votes[page] += weighted_confidence
            total_weight += weight
        
        # Normalize
        if not votes:
            return "unknown", 0.0
        
        best_page = max(votes, key=votes.get)
        best_confidence = votes[best_page] / total_weight
        
        return best_page, best_confidence
```

---

## Real-World Examples

### Roku Page Signatures

```python
ROKU_SIGNATURES = {
    "home": {
        "keywords": ["home hub", "my channels", "add channel"],
        "nav_buttons": 5,  # Home, Searches, Subscriptions, Settings, ...
        "motion_range": (0.0, 0.05),  # Usually static
    },
    "live_tv": {
        "keywords": ["live", "on now", "channels"],
        "nav_buttons": 4,
        "motion_range": (0.05, 0.25),  # Video is playing
    },
    "guide": {
        "keywords": ["guide", "what's on", "schedule"],
        "nav_buttons": 4,
        "motion_range": (0.01, 0.08),  # Scrolling through guide
    },
    "search": {
        "keywords": ["search", "show results", "found"],
        "nav_buttons": 3,
        "motion_range": (0.01, 0.05),  # Typing + results
    },
    "settings": {
        "keywords": ["settings", "about", "player"],
        "nav_buttons": 2,
        "motion_range": (0.0, 0.01),  # Static form
    },
}
```

### Apple TV Page Signatures

```python
APPLE_TV_SIGNATURES = {
    "up_next": {
        "keywords": ["up next", "continue watching"],
        "motion_range": (0.0, 0.05),
    },
    "watch_now": {
        "keywords": ["watch now", "personalized", "featured"],
        "motion_range": (0.0, 0.05),
    },
    "playback": {
        "keywords": ["playing", "play", "pause"],
        "motion_range": (0.08, 0.30),
    },
    "search": {
        "keywords": ["search", "results", "shows"],
        "motion_range": (0.0, 0.05),
    },
    "library": {
        "keywords": ["library", "watchlist", "purchases"],
        "motion_range": (0.01, 0.08),  # Scrolling through library
    },
}
```

---

## Performance Considerations

### Latency Budget
- **OCR:** ~500ms (too slow for real-time; run every 5 frames)
- **Layout detection:** ~10ms
- **Motion analysis:** <1ms
- **Total hybrid:** ~100ms (acceptable for most use cases)

### Optimization Checklist

- [ ] **Downscale frames** before OCR (e.g., 720p → 360p)
- [ ] **Region-based OCR** (nav bar only, not full frame)
- [ ] **Caching** (reuse page detection if motion is low)
- [ ] **Sampling** (OCR every Nth frame; layout every frame; motion always)
- [ ] **GPU acceleration** (OpenCV with CUDA if available)
- [ ] **Batch processing** (process multiple frames in parallel if using ML)

### Example Config

```python
@dataclass
class PageDetectionConfig:
    # OCR
    enable_ocr: bool = True
    ocr_sample_rate: int = 5  # Every 0.5 sec at 10 fps
    ocr_region: str = "top_nav"  # Full, top_nav, center
    
    # Layout
    enable_layout: bool = True
    layout_sample_rate: int = 1  # Every frame
    
    # Motion
    enable_motion: bool = True
    motion_window: int = 30  # 3 seconds
    
    # Fusion
    fusion_method: str = "weighted_vote"  # weighted_vote, max_confidence, consensus
```

---

## Testing & Validation

### Unit Tests

```python
def test_roku_home_page():
    """Test home page detection on Roku."""
    
    # Use a reference screenshot
    home_frame = cv2.imread("test_data/roku_home.png")
    
    detector = HybridPageDetector(platform="roku")
    page, confidence = detector.update(home_frame, motion=0.0)
    
    assert page == "home"
    assert confidence > 0.7

def test_playback_page():
    """Test live playback detection."""
    
    playback_frame = cv2.imread("test_data/roku_playback.png")
    
    detector = HybridPageDetector(platform="roku")
    page, confidence = detector.update(playback_frame, motion=0.15)
    
    assert page == "live_tv" or page == "playback"
    assert confidence > 0.6
```

### Manual Testing Workflow

1. **Capture reference images:** Screenshot each page at various resolutions
2. **Create test video:** Navigate through pages, record 30 sec per page
3. **Run detector:** Compare predictions vs. ground truth
4. **Fine-tune:** Adjust OCR keywords, motion thresholds, weights
5. **Validate:** Test on multiple devices (Roku firmware versions, UI changes)

---

## Troubleshooting

### Problem: OCR Has False Positives
**Solution:** Require multiple keywords to match, not just one
```python
# Before: any keyword match
if any(kw in text for kw in keywords):
    return page

# After: multiple keyword match
matches = [kw in text for kw in keywords]
if sum(matches) >= 2:  # At least 2 keywords
    return page
```

### Problem: Layout Detection Breaks After UI Update
**Solution:** Fall back to OCR; reduce weight on layout
```python
self.weights = {
    "ocr": 0.8,     # Increase
    "layout": 0.10, # Decrease
    "motion": 0.10,
}
```

### Problem: Motion-Based Detection Confuses Playback with Scrolling
**Solution:** Use variance, not just mean
```python
if mean > 0.05 and std < 0.05:  # High, stable motion = playback
    return "playback"
elif mean > 0.03 and std > 0.05:  # Variable motion = browsing
    return "browse"
```

### Problem: Slow OCR Performance
**Solution:** Downsample before OCR
```python
small_frame = cv2.resize(frame, (360, 240))
ocr_text = pytesseract.image_to_string(small_frame)
```

---

## Integration with Screen-to-Events

### Extended Observation Model

```python
@dataclass
class PagedObservation:
    t_video_ms: int
    page: str              # home, playback, browse, settings, search
    activity: str          # playback, buffering, paused, browsing, error
    page_confidence: float
    activity_confidence: float
    signals: Dict[str, object]

# Update classification
observation = PagedObservation(
    t_video_ms=5000,
    page="live_tv",
    activity="playback",
    page_confidence=0.85,
    activity_confidence=0.90,
    signals={
        "motion": 0.15,
        "ocr_page": "live_tv",
        "layout_page": "live_tv",
        "motion_page": "playback",
    }
)
```

### Validation Rules

```python
# Example: Telemetry says "search_query_submitted" 
# but observation shows page="home"
finding = Finding(
    severity="WARN",
    title="Page mismatch for search event",
    description="Search query submitted but page is home (expected: search)",
    observation_key=42,
    event_key=53,
)
```

---

## Next Steps

1. **Choose your platform:** Roku, Apple TV, Fire TV, or custom
2. **Build reference signatures:** OCR keywords + motion ranges
3. **Test on sample videos:** Validate detection accuracy
4. **Integrate into state machine:** Extend `classify_state()` to return (page, activity)
5. **Validate against telemetry:** Correlate page changes with navigation events

See [for-data-teams.md](for-data-teams.md) for integration examples.
