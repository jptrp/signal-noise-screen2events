# Roadmap

Vision and direction for Screen-to-Events.

## Current State (MVP, Jan 2026)

**✅ Implemented:**
- Vision-driven state machine (heuristic-based, explainable)
- Multi-platform telemetry adapters (S3, Athena, OpenSearch)
- Hardware automation & verification (Roku, Apple TV IR)
- Time alignment & correlation engine
- Evidence-backed findings with screenshot export
- Comprehensive documentation (WebDriver, page detection, data teams)

**Core Value:**
- Screen is ground truth
- Catch telemetry lying (latency, stalls, mismatches)
- No proprietary assumptions (generic, pluggable)

---

## Phase 2: Streaming & Real-Time (Q2–Q3 2026)

### Real-Time Analysis
- **Stream processing:** Process video/events as they arrive (not batch)
- **Live dashboards:** Monitor streaming health in real-time
- **Adaptive detection:** Adjust thresholds based on observed patterns
- **Alert integration:** Trigger alerts when mismatches detected

**Use case:** Monitoring production streaming quality 24/7 across fleet of devices

---

### Multi-Device Orchestration
- **Fleet coordination:** Run analysis across 10+ devices simultaneously
- **Aggregate insights:** Detect platform-wide issues (CDN region failure, codec support, etc.)
- **Device pooling:** Schedule tests across available inventory
- **Comparative analysis:** Same test on Roku vs. Apple TV vs. Fire TV

**Use case:** "Is this new codec working on all platforms?"

---

## Phase 3: Machine Learning & Confidence (Q3–Q4 2026)

### Optional ML State Detector
- **CNN-based state classifier:** Learn from labeled videos instead of hand-coded heuristics
- **Confidence scores:** ML model provides per-observation confidence
- **Adaptive training:** Improve over time with user feedback
- **Fallback to heuristics:** Use deterministic detector if ML uncertain

**Note:** Heuristic MVP remains the default. ML is optional enhancement.

**Use case:** Handling novel UI layouts without manual detector tweaks

---

### Temporal Models
- **LSTM-based event prediction:** Forecast likely next state based on history
- **Anomaly detection:** Flag unusual state transitions
- **User behavior modeling:** Distinguish intentional pauses from stalls

---

## Phase 4: Cloud & Scale (2027+)

### Cloud-Native Architecture
- **Distributed processing:** Offload heavy computation (OCR, ML inference) to cloud
- **Containerized pipeline:** Docker image for easy deployment
- **Kubernetes orchestration:** Auto-scaling for fleet testing
- **Cost optimization:** GPU instances for inference, spot instances for batch

---

### Public SaaS Option
- **Managed service:** Users upload video/config, get report without setup
- **Public leaderboards:** "Which streaming service has best latency?" (anonymized, opt-in)
- **API-driven:** Integrate with CI/CD pipelines, test automation frameworks

---

## Community & Contributions (Ongoing)

### Platform-Specific Detectors
Looking for contributions from teams using Screen-to-Events on:
- **Samsung TV / Tizen** — Page detection, IR mapping
- **Google TV / Android TV** — Specific UI patterns
- **PlayStation / Xbox** — Gaming console streaming
- **Custom apps** — Vertical-specific state machines

### Integrations
- **Prometheus metrics export** — Visualization in Grafana
- **ELK stack integration** — Feed findings into log analysis
- **DataDog/New Relic plugins** — Ingest alongside other metrics
- **WebDriver integration** — Automated test orchestration

### Documentation
- **Video tutorials** — Getting started, device setup, troubleshooting
- **Case studies** — "How Netflix uses Screen-to-Events," etc.
- **Research papers** — Publishing findings on telemetry accuracy

---

## Design Principles (All Phases)

1. **Screen is Truth** — Observational data always wins over claims
2. **Explainability** — No black boxes; decision trees not neural networks (unless optional)
3. **Vendor-Agnostic** — No lock-in to specific platforms or vendors
4. **Backward Compat** — New phases don't break existing pipelines
5. **Privacy First** — All analysis local; no telemetry sent upstream (unless explicitly configured)

---

## Known Non-Goals

❌ **Real-world video testing:** (UX testing tools like BrowserStack exist)  
❌ **Synthetic test generation:** (load testing tools like k6 exist)  
❌ **UI automation framework:** (Playwright, WebdriverIO exist)  
❌ **Telemetry collection:** (Only validates existing telemetry)

---

## How to Contribute

### Code Contributions
1. Check [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines
2. Pick an issue or propose a feature
3. Follow the adapter pattern for new telemetry sources
4. Add tests; update docs

### Feedback & Ideas
- **GitHub Discussions:** Share use cases, ask questions
- **Issues:** Report bugs or request features
- **Security:** Report vulnerabilities privately to jptrp@icloud.com

### Device Support
Have a Roku/Apple TV/Fire Stick? Help us:
1. Test the pipeline on your device
2. Contribute improved IR command mappings
3. Share sample videos for algorithm tuning

---

## Estimated Timeline

| Phase | Period | Key Deliverables |
|-------|--------|------------------|
| **MVP** | Jan 2026 | Heuristic detectors, S3 adapter, documentation |
| **Phase 2** | Q2–Q3 2026 | Streaming, multi-device, real-time dashboards |
| **Phase 3** | Q3–Q4 2026 | ML state detector (optional), temporal models |
| **Phase 4** | 2027 | Cloud architecture, managed SaaS, scale |

---

## Latest Updates

- **Jan 15, 2026:** Published Screen-to-Events v1.0 (MVP)
  - Heuristic state machine, 3 telemetry adapters
  - Roku + Apple TV IR support
  - Comprehensive documentation
