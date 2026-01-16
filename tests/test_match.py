from screen2events.models import Alignment, NormalizedEvent, Observation, UXState
from screen2events.correlate.match import match_events_to_screen


def test_match_basic():
    obs = [
        Observation(t_video_ms=0, state=UXState.APP_OPEN, confidence=1.0),
        Observation(t_video_ms=8000, state=UXState.PLAYBACK, confidence=1.0),
    ]
    events = [
        NormalizedEvent(t_event_ms=1000, kind="session_start"),
        NormalizedEvent(t_event_ms=9000, kind="playback"),
    ]
    # alignment offset = +1000 ms (event = video + 1000)
    aln = Alignment(offset_ms=1000)
    matches = match_events_to_screen(observations=obs, events=events, alignment=aln)
    assert any(m["event_kind"] == "playback" and m["match"] for m in matches)
