# Sample Correlation Report

**Session:** roku_session_20260115_001  
**Device:** Roku (model f35d41)  
**Duration:** 180 seconds (3 minutes)  
**Run Date:** 2026-01-15 14:30:00 UTC  

---

## Summary

✅ **Telemetry Alignment: GOOD**
- Offset: +50ms (event clock is 50ms ahead of video clock)
- Drift: 1000 ppm (0.1% — acceptable)
- Events matched: 10/10
- Findings: 2 (1 INFO, 1 WARN)

**Interpretation:** Telemetry is mostly reliable. Two minor timing discrepancies noted; video confirms playback worked as expected.

---

## Timeline

```
0ms          Home screen displayed
2000ms       [EVENT] session_start
3500ms       [EVENT] browse_start → User navigates to Live TV
8000ms       [EVENT] content_selected (NBC)
9500ms       [EVENT] playback_start
9500ms       [OBS]   Buffering state detected
9000ms       [OBS]   Playback motion detected (500ms before event!)
⚠️  FINDING: Event fired early vs. observation

65000ms      [EVENT] buffering_start
65000ms      [OBS]   Buffering state (motion drops to 0%)
            Network stall detected; recovered after 3 seconds

68000ms      [EVENT] buffering_end
68500ms      [OBS]   Playback resumes

95000ms      [EVENT] ad_start (30-second ad)
95500ms      [OBS]   Ad state detected; "skip ad" button visible

126000ms     [EVENT] ad_end
126500ms     [OBS]   Playback resumes
⚠️  FINDING: UI still showing "skip ad" for 3 more seconds

150000ms     [EVENT] pause
150000ms     [OBS]   Paused state confirmed (motion = 0)
```

---

## Key Observations

### ✅ What Worked Well
- **Session initialization:** Clean app open, telemetry synchronized
- **Content selection:** State transitions matched telemetry events
- **Ad delivery:** Ad started/ended as expected
- **Playback quality:** Sustained motion during playback (avg 0.14)

### ⚠️ Minor Issues
1. **Event timing variance:** `playback_start` event fired 500ms *before* video motion detected
   - Likely: Event batching or early firing by SDK
   - Impact: Low (within acceptable range)
   - Action: Monitor in future runs; may warrant investigation if consistent

2. **Ad UI lag:** "Skip ad" button remained visible 3 seconds after `ad_end` event
   - Likely: Asynchronous UI update on streaming device
   - Impact: Low (ad didn't actually play past end)
   - Action: Acceptable; UI lag is common on embedded devices

---

## Telemetry Quality Score

| Metric | Score | Notes |
|--------|-------|-------|
| **Timing Accuracy** | 95% | ±50ms offset, <0.1% drift |
| **Completeness** | 100% | All expected events present |
| **State Alignment** | 98% | 2 minor discrepancies, both explainable |
| **Latency Capture** | 90% | Buffering detected; recover time accurate |
| **Overall Grade** | **A** | Production-ready telemetry |

---

## Evidence

### Playback Start Timing (Finding #1)

**Video observation:**
```
t_video=9000ms: motion=0.15, state=playback → Video started
```

**Telemetry event:**
```
t_event=9500ms: kind=playback_start → Event fired
```

**Analysis:** Event fired 500ms *after* playback was already visible. Possible causes:
- Event batching in SDK (batches every 500ms)
- Event fired before stream decoder ready
- Clock offset (ruled out; align model handles this)

**Verdict:** Acceptable. Video confirms playback worked; event timing is within normal variance.

---

### Ad Skip UI Lag (Finding #2)

**Telemetry event:**
```
t_event=126000ms: kind=ad_end
```

**Video observation:**
```
t_video=126500ms: ocr_text="skip ad" (still visible)
t_video=129500ms: ocr_text="" (button finally hidden)
```

**Analysis:** UI took 3 seconds to hide the skip button after event fired. This is typical on streaming devices where UI updates are asynchronous.

**Verdict:** Not a problem. Ad content ended as expected; UI just lagged.

---

## Recommendations

1. **Continue monitoring this device:** Playback start timing variance worth tracking
2. **Set baselines:** Use this run as reference for future comparisons
3. **Network conditions:** Buffering event shows network was good (quick recovery); keep monitoring
4. **Next validation:** Repeat with different content/time of day to rule out transient issues

---

## Next Steps

- ✅ Run passed validation
- 📊 Compare against baseline in next session
- 🔔 Alert if findings escalate to ERROR severity
- 📁 Archive evidence for 30 days
