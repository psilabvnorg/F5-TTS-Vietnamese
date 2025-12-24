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
  - Title: "F5-TTS Voice Cloning" / "F5-TTS Nhân Bản Giọng Nói"
  - Language toggle button (top-right): VN/EN switcher
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
- LanguageToggle
  - Props: currentLang, onToggle
  - State: language ('vi' | 'en')
  - Position: fixed top-right corner
  - Display: Flag icons or VN/EN text button
- VoiceSelector
  - Props: voices[] (id, name, description, thumbnail), language
  - State: selectedVoiceId
  - Displays localized voice names and descriptions
- TextInput
  - Props: maxChars (500), placeholder (localized)
  - State: text, charCount
  - Display character counter below input (e.g., "250/500")
  - Warning message when text exceeds 500 chars:
    - Vietnamese
    - English:
- GenerateButton
  - Disabled states: invalid form, generating
  - Label: "Generate" / "Tạo giọng nói"
- AudioPlayer
  - Props: src, autoPlay
  - Localized controls and labels (localized messages)
- Persist last selection/text/language preference in localStorage
- Language preference saved and restored on revisit
- All UI labels, placeholders, messages, and errors localized
  - Props: samples[] (id, title, src), language
  - Displays localized sample titles and descriptions

## Validation & UX
- Require voice selection and non-empty text
- Limit text length to 500 characters (only first 500 chars will be processed)
- Display warning message below text input when text exceeds 500 characters
- Character counter shows current/max (e.g., "523/500" in red when exceeded)
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
- MInternationalization (i18n)
- Supported languages: Vietnamese (vi), English (en)
- Default language: Vietnamese
- Translation keys for all UI strings:
  - Navigation and headers
  - Form labels and placeholders
  - Button text and tooltips
  - Error and success messages
  - Sample titles and descriptions
- Language toggle persists across sessions
- Consider dynamic content translation from backend (voice names, descriptions)

## Translation Coverage
### Vietnamese (vi)
- App title: "F5-TTS Nhân Bản Giọng Nói"
- Generate button: "Tạo giọng nói"
- Text placeholder: "Nhập văn bản cần chuyển đổi..."
- Voice selector: "Chọn giọng nói"
- Download: "Tải xuống"
- Status: "Trực tuyến" / "Đang xử lý"
- Character limit warning message

### English (en)
- App title: "F5-TTS Voice Cloning"
- Generate button: "Generate"
- Text placeholder: "Enter text to synthesize..."
- Voice selector: "Select voice"
- Download: "Download"
- Status: "Online" / "Busy"
- Character limit warning message

## Future Enhancements
- Upload custom reference audio
- Advanced controls: speed, silence removal, CFG, NFE
- Job progress via WebSocket
- Save sessions/history and share links
