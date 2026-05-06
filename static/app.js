document.addEventListener('DOMContentLoaded', () => {
    // Check if user has a token in cookies (rudimentary check, actual auth is backend)
    const hasToken = document.cookie.includes('webex_token=');
    const authSection = document.getElementById('authSection');
    
    // Check login status
    async function checkLogin() {
        try {
            const response = await fetch('/me');
            if (response.ok) {
                const data = await response.json();
                authSection.innerHTML = `
                    <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success-color); border-radius: 12px; padding: 1rem;">
                        <p style="margin-bottom: 0.5rem; color: var(--success-color);">
                            <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                            Logged in successfully
                        </p>
                        <p style="font-weight: 600;">${data.name}</p>
                        <p style="font-size: 0.875rem; color: var(--text-secondary);">${data.email}</p>
                    </div>
                `;
            }
        } catch (e) {
            console.error('Not logged in:', e);
        }
    }
    
    // Check auth on load
    checkLogin();

    // UI Elements
    const recordBtn = document.getElementById('recordBtn');
    const stopBtn = document.getElementById('stopBtn');
    const playbackSection = document.getElementById('playbackSection');
    const audioPlayback = document.getElementById('audioPlayback');
    const retakeBtn = document.getElementById('retakeBtn');
    const uploadBtn = document.getElementById('uploadBtn');
    const visualizer = document.getElementById('visualizer');
    const statusMessage = document.getElementById('statusMessage');
    const statusText = document.getElementById('statusText');
    const spinner = document.getElementById('spinner');

    let mediaRecorder;
    let audioChunks = [];
    let audioBlob;

    // Initialize MediaRecorder
    async function initAudio() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.addEventListener('dataavailable', event => {
                audioChunks.push(event.data);
            });

            mediaRecorder.addEventListener('stop', () => {
                audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const audioUrl = URL.createObjectURL(audioBlob);
                audioPlayback.src = audioUrl;
                
                // Update UI
                recordBtn.classList.add('hidden');
                stopBtn.classList.add('hidden');
                visualizer.classList.remove('recording');
                playbackSection.classList.remove('hidden');
            });
        } catch (err) {
            console.error('Error accessing microphone:', err);
            showStatus('Error accessing microphone. Please ensure permissions are granted.', true);
        }
    }

    recordBtn.addEventListener('click', async () => {
        if (!mediaRecorder) await initAudio();
        if (mediaRecorder) {
            audioChunks = [];
            mediaRecorder.start();
            recordBtn.classList.add('hidden');
            stopBtn.classList.remove('hidden');
            visualizer.classList.add('recording');
            playbackSection.classList.add('hidden');
        }
    });

    stopBtn.addEventListener('click', () => {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
        }
    });

    retakeBtn.addEventListener('click', () => {
        playbackSection.classList.add('hidden');
        recordBtn.classList.remove('hidden');
        audioChunks = [];
        audioBlob = null;
    });

    uploadBtn.addEventListener('click', async () => {
        if (!audioBlob) return;

        // Show uploading state
        playbackSection.classList.add('hidden');
        showStatus('Processing audio and uploading to Webex...', false, true);

        const formData = new FormData();
        // The backend expects 'audio_file'
        formData.append('audio_file', audioBlob, 'greeting.webm');

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                showStatus('Success! Your voicemail greeting has been updated.', false, false);
                // Reset UI after 3 seconds
                setTimeout(() => {
                    statusMessage.classList.add('hidden');
                    recordBtn.classList.remove('hidden');
                    audioChunks = [];
                    audioBlob = null;
                }, 3000);
            } else {
                throw new Error(result.detail || 'Upload failed');
            }
        } catch (error) {
            console.error('Upload error:', error);
            showStatus(`Error: ${error.message}`, true, false);
            playbackSection.classList.remove('hidden');
        }
    });

    function showStatus(message, isError = false, showSpinner = false) {
        statusMessage.classList.remove('hidden');
        statusText.textContent = message;
        statusText.style.color = isError ? 'var(--danger-color)' : 'var(--text-primary)';
        
        if (showSpinner) {
            spinner.classList.remove('hidden');
        } else {
            spinner.classList.add('hidden');
        }
    }
});
