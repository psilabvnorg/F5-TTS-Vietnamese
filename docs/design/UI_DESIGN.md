# UI Design: F5-TTS Vietnamese Workflow

1. User selects from available preset voices.
2. User enters the text to be voice-cloned.
3. User clicks a Generate button to produce a WAV file.
4. Provide a Download button for the generated audio.
5. UI displays several pre-made output WAV samples for users to click and preview.

## User Flows
- Generate TTS
  - Select preset voice → Enter text → Click Generate → Hear preview → Download WAV
- Preview Samples
  - Click any sample card → Inline audio player plays the sample

## Screen Layout
- Header
  - Title: "F5-TTS Voice Cloning"
  - Status pill (Online/Busy)
- Main Form
  - Voice selector: dropdown or cards with avatar/name
  - Text input: multiline textarea with character counter
  - Actions: Generate (primary), Reset (secondary)
  - Result: inline audio player + Download button when ready
- Samples Section
  - Grid of sample cards (voice name + short description)
  - Each card has Play/Pause audio control

## Components
- VoiceSelector
  - Props: voices[] (id, name, description, thumbnail)
  - State: selectedVoiceId
- TextInput
  - Props: maxChars, placeholder
  - State: text
- GenerateButton
  - Disabled states: invalid form, generating
- AudioPlayer
  - Props: src, autoPlay
- SampleGrid
  - Props: samples[] (id, title, src)

## Validation & UX
- Require voice selection and non-empty text
- Limit text length (configurable, e.g., 1–1,000 chars)
- Loading state with progress indicator during generation
- Error toast on API failure with retry option
- Persist last selection/text in localStorage (optional)

## API Integration (FastAPI)
- Endpoint: `POST /tts`
  - `multipart/form-data`: `text`, `voice_id` or `voice_file` (future), optional params
  - Response: `audio/wav` stream (sync) or `{ job_id }` (async)
- Endpoint: `GET /jobs/{id}` (if async)
- Static samples: served via CDN/object storage or `GET /samples`

## Accessibility
- Keyboard navigation for all controls
- Visible focus states
- Labels for inputs and clear error messages
- Audio controls accessible via screen readers

## Mobile/Responsive
- Single-column layout on mobile
- Responsive audio player controls
- Touch-friendly buttons

## Styling
- Neutral theme with emphasis on primary action
- Cards for voices and samples with hover/active states
- Show generation time and file size when available

## Metrics
- Generation requests, success/error rates
- Average latency and audio duration
- Most selected voices, top sample plays

## Future Enhancements
- Upload custom reference audio
- Advanced controls: speed, silence removal, CFG, NFE
- Job progress via WebSocket
- Save sessions/history and share links
