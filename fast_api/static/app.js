(() => {
  const form = document.getElementById('tts-form');
  const statusEl = document.getElementById('status');
  const resultEl = document.getElementById('result');
  const audioEl = document.getElementById('audio-player');
  const downloadEl = document.getElementById('download-link');
  const messageEl = document.getElementById('message');
  const samplesEl = document.getElementById('samples');
  const generateBtn = document.getElementById('generate-btn');
  const voiceSelect = document.getElementById('voice-select');
  const voiceInfoEl = document.getElementById('voice-info');
  const voiceNameEl = document.getElementById('voice-name');
  const voiceDescEl = document.getElementById('voice-description');
  const voiceMetaEl = document.getElementById('voice-meta');
  
  // Loading modal elements
  const loadingModal = document.getElementById('loading-modal');
  const progressPercent = document.getElementById('progress-percent');
  const progressBar = document.getElementById('progress-bar');
  const progressText = document.getElementById('progress-text');

  function showLoadingModal() {
    resetLoadingModal();
    loadingModal.classList.remove('hidden');
  }

  function hideLoadingModal() {
    loadingModal.classList.add('hidden');
  }

  function updateProgress(percent, text = '') {
    progressPercent.textContent = `${Math.round(percent)}%`;
    progressBar.style.width = `${percent}%`;
    if (text) {
      progressText.textContent = text;
    }
  }

  function showCompletionState() {
    const spinner = document.getElementById('spinner');
    const progressPercent = document.getElementById('progress-percent');
    const progressText = document.getElementById('progress-text');
    const progressBar = document.getElementById('progress-bar');
    const loadingSubtitle = document.getElementById('loading-subtitle');
    const okBtn = document.getElementById('modal-ok-btn');
    
    // Hide spinner and progress elements
    spinner.style.display = 'none';
    progressBar.parentElement.style.display = 'none';
    loadingSubtitle.style.display = 'none';
    
    // Show completion message
    progressPercent.textContent = '✓';
    progressPercent.classList.add('text-success');
    progressText.textContent = 'Đã hoàn thành tạo file, kiểm tra ở phần Kết quả bên dưới.';
    
    // Show OK button
    okBtn.classList.remove('hidden');
  }

  function resetLoadingModal() {
    const spinner = document.getElementById('spinner');
    const progressPercent = document.getElementById('progress-percent');
    const progressBar = document.getElementById('progress-bar');
    const loadingSubtitle = document.getElementById('loading-subtitle');
    const okBtn = document.getElementById('modal-ok-btn');
    
    // Reset all elements to initial state
    spinner.style.display = 'block';
    progressBar.parentElement.style.display = 'block';
    loadingSubtitle.style.display = 'block';
    progressPercent.classList.remove('text-success');
    okBtn.classList.add('hidden');
    
    updateProgress(0, 'Đang khởi tạo...');
  }

  async function checkHealth() {
    try {
      const res = await fetch('/healthz');
      if (res.ok) {
        const data = await res.json();
        statusEl.textContent = `API status: online (v${data.version || '1.0.0'})`;
      } else {
        statusEl.textContent = 'API status: offline';
      }
    } catch (e) {
      statusEl.textContent = 'API status: offline';
    }
  }

  function setMessage(text, type = 'info') {
    if (!text) {
      messageEl.textContent = '';
      messageEl.className = '';
      return;
    }
    
    // Map types to DaisyUI alert classes
    const alertClasses = {
      'info': 'alert alert-info',
      'success': 'alert alert-success',
      'error': 'alert alert-error'
    };
    
    messageEl.textContent = text;
    messageEl.className = alertClasses[type] || 'alert';
  }

  async function loadVoices() {
    try {
      const res = await fetch('/voices');
      if (!res.ok) {
        throw new Error('Failed to load voices');
      }
      
      const data = await res.json();
      voiceSelect.innerHTML = '';
      
      if (data.voices && data.voices.length > 0) {
        data.voices.forEach(voice => {
          const option = document.createElement('option');
          option.value = voice.id;
          option.textContent = `${voice.name} (${voice.gender})`;
          option.title = voice.description;
          voiceSelect.appendChild(option);
        });
        
        // Load samples from backend
        loadSamplesFromBackend();
        
        // Load detail for first voice
        if (data.voices.length > 0) {
          loadVoiceDetail(data.voices[0].id);
        }
      } else {
        voiceSelect.innerHTML = '<option value="">Không có giọng nào</option>';
      }
    } catch (e) {
      console.error('Error loading voices:', e);
      voiceSelect.innerHTML = '<option value="">Lỗi tải giọng</option>';
      setMessage('Không thể tải danh sách giọng', 'error');
    }
  }

  async function loadSamplesFromBackend() {
    samplesEl.innerHTML = '';
    try {
      const res = await fetch('/samples');
      if (!res.ok) throw new Error('Failed to load samples');
      const data = await res.json();
      const samples = data.samples || [];
      if (samples.length === 0) {
        samplesEl.innerHTML = '<p class="text-center opacity-50">Chưa có mẫu audio nào</p>';
        return;
      }
      samples.forEach(item => {
        const card = document.createElement('div');
        card.className = 'card bg-base-200 shadow-md';
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body p-4';
        const title = document.createElement('h3');
        title.className = 'card-title text-base';
        title.textContent = item.voice.replace(/_/g, ' ');
        const sub = document.createElement('p');
        sub.className = 'text-xs opacity-70';
        sub.textContent = item.filename;
        const audio = document.createElement('audio');
        audio.controls = true;
        audio.className = 'w-full mt-2';
        audio.src = item.url;
        cardBody.appendChild(title);
        cardBody.appendChild(sub);
        cardBody.appendChild(audio);
        card.appendChild(cardBody);
        samplesEl.appendChild(card);
      });
    } catch (e) {
      console.error('Error loading samples:', e);
      samplesEl.innerHTML = '<p class="text-center text-error">Lỗi tải mẫu audio</p>';
    }
  }

  async function loadSamples() {
    // This function is now replaced by loadSamplesFromVoices
    // Kept for backward compatibility if needed
  }

  async function loadVoiceDetail(voiceId) {
    if (!voiceId) {
      voiceInfoEl.classList.add('hidden');
      return;
    }

    try {
      const res = await fetch(`/voices/${voiceId}`);
      if (!res.ok) {
        throw new Error('Failed to load voice details');
      }

      const voice = await res.json();
      
      // Update voice info display
      voiceNameEl.textContent = voice.name;
      voiceDescEl.textContent = voice.description;
      voiceMetaEl.textContent = `${voice.language.toUpperCase()} • ${voice.gender === 'male' ? 'Nam' : 'Nữ'}`;
      
      voiceInfoEl.classList.remove('hidden');
    } catch (e) {
      console.error('Error loading voice details:', e);
      voiceInfoEl.classList.add('hidden');
    }
  }

  // Listen for voice selection change
  voiceSelect.addEventListener('change', (e) => {
    loadVoiceDetail(e.target.value);
  });

  // Character counter
  const textInput = document.getElementById('text-input');
  const charCount = document.getElementById('char-count');
  
  textInput.addEventListener('input', () => {
    const len = textInput.value.length;
    charCount.textContent = `${len} / 5000`;
    if (len > 5000) {
      charCount.classList.add('text-error', 'font-semibold');
    } else {
      charCount.classList.remove('text-error', 'font-semibold');
    }
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    setMessage('');
    generateBtn.disabled = true;
    
    // Show loading modal
    showLoadingModal();

    try {
      const fd = new FormData(form);
      const text = fd.get('text');
      const voiceId = fd.get('voice_id');
      const speed = fd.get('speed') || '1.0';
      const cfgStrength = fd.get('cfg_strength') || '2.0';
      const nfeStep = fd.get('nfe_step') || '32';
      const removeSilence = fd.get('remove_silence') === 'on';

      if (!text) {
        setMessage('Vui lòng nhập text.', 'error');
        generateBtn.disabled = false;
        hideLoadingModal();
        return;
      }

      if (text.length > 5000) {
        setMessage('Văn bản không được vượt quá 5000 ký tự.', 'error');
        generateBtn.disabled = false;
        hideLoadingModal();
        return;
      }

      if (!voiceId) {
        setMessage('Vui lòng chọn giọng.', 'error');
        generateBtn.disabled = false;
        hideLoadingModal();
        return;
      }

      // Build SSE request URL
      const params = new URLSearchParams();
      params.append('text', text);
      params.append('voice_id', voiceId);
      params.append('speed', speed);
      params.append('cfg_strength', cfgStrength);
      params.append('nfe_step', nfeStep);
      params.append('remove_silence', removeSilence);

      // Use Server-Sent Events for real-time progress
      const eventSource = new EventSource(`/tts/generate-audio?${params.toString()}`);
      
      eventSource.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.error) {
            eventSource.close();
            hideLoadingModal();
            setMessage(data.error, 'error');
            generateBtn.disabled = false;
            return;
          }
          
          // Update progress with real backend data
          updateProgress(data.progress, data.status);
          
          // If complete, handle audio data
          if (data.progress === 100 && data.audio_data) {
            eventSource.close();
            
            // Decode base64 audio
            const audioBytes = atob(data.audio_data);
            const audioArray = new Uint8Array(audioBytes.length);
            for (let i = 0; i < audioBytes.length; i++) {
              audioArray[i] = audioBytes.charCodeAt(i);
            }
            const blob = new Blob([audioArray], { type: 'audio/wav' });
            const url = URL.createObjectURL(blob);
            
            audioEl.src = url;
            downloadEl.href = url;
            downloadEl.download = data.filename || 'output.wav';
            
            // Show completion state with OK button
            showCompletionState();
            
            // When modal closes (via OK button), show results
            const okBtn = document.getElementById('modal-ok-btn');
            okBtn.onclick = () => {
              hideLoadingModal();
              resetLoadingModal();
              resultEl.classList.remove('hidden');
              
              // Show success with metrics
              let successMsg = 'Tạo audio thành công!';
              if (data.duration) successMsg += ` • Độ dài: ${data.duration.toFixed(1)}s`;
              if (data.file_size) successMsg += ` • Kích thước: ${(data.file_size / 1024).toFixed(0)}KB`;
              setMessage(successMsg, 'success');
            };
            
            generateBtn.disabled = false;
          }
        } catch (err) {
          console.error('Error parsing SSE data:', err);
        }
      };
      
      eventSource.onerror = (err) => {
        console.error('SSE error:', err);
        eventSource.close();
        hideLoadingModal();
        setMessage('Có lỗi xảy ra khi tạo audio. Vui lòng thử lại.', 'error');
        generateBtn.disabled = false;
      };
      
    } catch (err) {
      console.error(err);
      hideLoadingModal();
      setMessage(err.message || 'Có lỗi xảy ra.', 'error');
      generateBtn.disabled = false;
    }
  });

  // Init
  checkHealth();
  loadVoices();
})();
