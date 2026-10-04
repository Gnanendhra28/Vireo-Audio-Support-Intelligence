# VIDEO RECORDING & TECHNICAL SETUP CHECKLIST
**Project:** Vireo Audio Support Intelligence  
**Phase:** Step 6 — Video Demonstration Operational Protocol  
**Target Duration:** Strictly $\le$ 3 Minutes (180 Seconds)  
**Output Target:** `outputs/recordings/demo_recording.mp4` (or uploaded video link)  

---

## 1. Pre-Recording System & Environment Setup

- [ ] **Python Environment Verification:**
  - Verify Python 3.11+ is active:
    ```bash
    python3 --version
    ```
  - Verify required libraries are installed:
    ```bash
    pip install -r requirements.txt
    ```
- [ ] **Launch Dashboard Application:**
  - Start Streamlit from the project directory:
    ```bash
    streamlit run app.py
    ```
  - Confirm the terminal prints local URL: `http://localhost:8501`.
  - Open `http://localhost:8501` in Google Chrome or Chromium.
- [ ] **Display & Window Cleanliness:**
  - Use a clean browser profile or Incognito window with extensions disabled.
  - Set browser zoom to 100% and window resolution to 1080p (1920 × 1080) or 1440 × 900.
  - Hide bookmarks bar (`Cmd + Shift + B` on macOS).
  - Collapse unnecessary system dock/taskbars or record application window only.
- [ ] **Privacy & Distraction Controls:**
  - Enable **Do Not Disturb / Focus Mode** on macOS (`System Settings > Focus > Do Not Disturb`).
  - Close Slack, WhatsApp, email clients, and messaging notifications.
  - Hide personal desktop files or icons.
- [ ] **Audio & Hardware Check:**
  - Test external microphone or built-in mic with 10-second test clip to ensure crisp, audible audio without background hiss or fan noise.
  - Ensure room is quiet and echo-free.

---

## 2. In-Recording Execution Protocol

- [ ] **Adhere to the 3-Minute Hard Ceiling:**
  - Start stopwatch on second screen or phone when recording starts.
  - Section-by-section time benchmarks (from `outputs/reports/demo_script.md`):
    - **0:00 – 0:20:** The Business Problem (Priya's core question)
    - **0:20 – 0:50:** Executive Overview (11,641 tickets, status donut, Diwali peak)
    - **0:50 – 1:20:** Category & Routing Analysis (Billing misroutes, 696 hand-offs)
    - **1:20 – 1:50:** Team Workload (Logistics 28.6 tix/mo & 26h vs. Billing 1.22h)
    - **1:50 – 2:20:** Financial Impact (Friction, SLA credits, ₹2L hypothetical savings)
    - **2:20 – 2:45:** Recommendation (Reject Billing, conditional 1 Logistics hire, 90d hold)
    - **2:45 – 3:00:** Closing (90-day targets: 75% hand-off cut, 90% SLA, $\le 18$h delay)
- [ ] **Smooth View Navigation:**
  - Click cleanly on the sidebar navigation options.
  - Allow Plotly charts 1 second to settle before speaking on them.
  - Use smooth scroll down the page rather than jumping.
- [ ] **Pronunciation & Metric Accuracy:**
  - State **11,641 core tickets** (not 11,780, which includes 2024 pilot).
  - State **696 core hand-offs** (not 795, which includes 2024 pilot).
  - State **-627 Billing net delta** (1,798 resolved vs. 2,425 assigned).
  - State **+35.1% Logistics expansion** (2,574 resolved vs. 1,905 assigned).
  - Clearly qualify process savings as **hypothetical operational reductions**.

---

## 3. Post-Recording Quality Verification

- [ ] **File Presence & Integrity:**
  - Save video file into `outputs/recordings/` (e.g., `outputs/recordings/vireo_demo_walkthrough.mp4`).
  - Verify the file is not corrupted and has a valid file size (typically 15 MB – 80 MB for 3 minutes).
- [ ] **Playback & Duration Verification:**
  - Open video in QuickTime, VLC, or browser.
  - Verify total video duration is strictly **$\le 3$ minutes 00 seconds** (e.g., 2:50 is ideal).
  - Verify audio sync and visual sharpness (text and numbers on cards must be crisp and legible).
- [ ] **Zero-Fabrication Commitment:**
  - Do NOT claim that the video recording has been captured or submitted until the actual MP4 file is generated and verified on disk.
  - Do NOT create mock video placeholders or synthetic transcripts masquerading as actual recording files.

---

## 4. Submission Packaging

- [ ] Video file ready or uploaded to Loom / Google Drive / unlisted YouTube (with sharing permissions set to "Anyone with the link can view").
- [ ] URL or local file path recorded in the final submission notes.
- [ ] All code, test suite, and reports intact in the repository.
