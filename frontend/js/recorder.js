/**
 * VOX - Browser Audio Recording Module
 * Manages MediaRecorder API, microphone permissions, real-time timer,
 * audio blob packaging, and visual recording states.
 */

const VoiceRecorder = {
    mediaRecorder: null,
    speechRecognizer: null,
    recognizedTranscript: '',
    audioChunks: [],
    audioStream: null,
    recordingTimerInterval: null,
    recordingStartTime: null,
    recordingDurationSeconds: 0,
    isRecording: false,
    isProcessing: false,
    maxDurationSeconds: 60, // Auto-stop limit for safety

    // DOM Elements
    elements: {
        card: null,
        toggleBtn: null,
        stopBtn: null,
        statusText: null,
        timerText: null,
        soundWave: null,
    },

    /**
     * Initialize recorder module and bind UI listeners
     */
    init() {
        this.elements.card = document.getElementById('recorder-card');
        this.elements.toggleBtn = document.getElementById('mic-toggle-btn');
        this.elements.stopBtn = document.getElementById('mic-stop-btn');
        this.elements.statusText = document.getElementById('recorder-status');
        this.elements.timerText = document.getElementById('recorder-timer');
        this.elements.soundWave = document.getElementById('sound-wave');

        if (!this.elements.toggleBtn) return;

        // Toggle record button
        this.elements.toggleBtn.addEventListener('click', () => {
            if (this.isProcessing) return;
            if (this.isRecording) {
                this.stopRecording();
            } else {
                this.startRecording();
            }
        });

        // Dedicated stop button
        if (this.elements.stopBtn) {
            this.elements.stopBtn.addEventListener('click', () => {
                if (this.isRecording) {
                    this.stopRecording();
                }
            });
        }
    },

    /**
     * Detect best supported audio MIME type in current browser
     */
    getSupportedMimeType() {
        const candidateTypes = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/ogg;codecs=opus',
            'audio/wav',
            'audio/mp4',
        ];

        for (const type of candidateTypes) {
            if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }
        return '';
    },

    /**
     * Request microphone access and start recording
     */
    async startRecording() {
        // Check browser support
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            showToast('Audio recording is not supported in this browser.', 'error');
            this.setStatus('Microphone unsupported', 'error');
            return;
        }

        try {
            this.setStatus('Requesting microphone permission...', 'idle');

            // Request microphone audio stream
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                }
            });

            const mimeType = this.getSupportedMimeType();
            const options = mimeType ? { mimeType } : {};

            this.mediaRecorder = new MediaRecorder(this.audioStream, options);
            this.audioChunks = [];
            this.recognizedTranscript = '';

            // Event: Chunks of audio data arrive
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            // Event: Recording stopped
            this.mediaRecorder.onstop = () => {
                this.handleRecordingComplete(mimeType);
            };

            // Start browser Speech Recognition in parallel (for real-time speech-to-text)
            const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (SpeechRec) {
                try {
                    this.speechRecognizer = new SpeechRec();
                    this.speechRecognizer.continuous = true;
                    this.speechRecognizer.interimResults = true;

                    // Support automatic language detection or explicit language selection
                    const langSelect = document.getElementById('pref-speech-language');
                    const chosenLang = langSelect ? langSelect.value : 'auto';
                    if (chosenLang && chosenLang !== 'auto') {
                        this.speechRecognizer.lang = chosenLang;
                    } else {
                        // Default to browser / system locale for automatic language detection
                        this.speechRecognizer.lang = navigator.language || 'en-US';
                    }

                    this.speechRecognizer.onresult = (event) => {
                        let fullText = '';
                        for (let i = 0; i < event.results.length; i++) {
                            fullText += event.results[i][0].transcript + ' ';
                        }
                        this.recognizedTranscript = fullText.trim();
                        if (this.recognizedTranscript) {
                            this.setStatus(`Listening: <em>"${escapeHtml(this.recognizedTranscript)}"</em>`, 'recording');
                        }
                    };

                    // Auto-stop when speech finishes
                    this.speechRecognizer.onspeechend = () => {
                        if (this.recognizedTranscript && this.isRecording) {
                            setTimeout(() => {
                                if (this.isRecording) {
                                    console.log('SpeechRecognizer detected speech end; auto-stopping...');
                                    this.stopRecording();
                                }
                            }, 1200);
                        }
                    };

                    this.speechRecognizer.onerror = (event) => {
                        console.warn('Speech recognition warning:', event.error);
                    };

                    this.speechRecognizer.start();
                } catch (recErr) {
                    console.warn('Could not start speech recognition:', recErr);
                }
            }

            // Start Voice Activity Detection (VAD) for auto-stop on silence
            this.startVoiceActivityDetection(this.audioStream);

            // Start recording (gather chunks every 250ms)
            this.mediaRecorder.start(250);
            this.isRecording = true;
            this.recordingStartTime = Date.now();

            // UI update to active recording state
            this.elements.card.classList.add('recording');
            this.setStatus('Listening... (speak naturally, stops automatically on pause)', 'recording');
            this.startTimer();

            showToast('Listening... Speak your task naturally.', 'info', 2000);

        } catch (error) {
            console.error('Microphone access failed:', error);
            this.handleMicrophoneError(error);
        }
    },

    /**
     * Voice Activity Detection (VAD)
     * Monitors volume and automatically stops recording after user finishes speaking.
     */
    startVoiceActivityDetection(stream) {
        try {
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            if (!AudioContextClass) return;

            this.audioContext = new AudioContextClass();
            const source = this.audioContext.createMediaStreamSource(stream);
            const analyser = this.audioContext.createAnalyser();
            analyser.fftSize = 256;
            source.connect(analyser);

            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);

            let userStartedSpeaking = false;
            let silenceStartTime = null;
            let noiseFloorSamples = 0;
            let noiseFloorSum = 0;
            let ambientNoiseFloor = 8;
            const calibrationStartTime = Date.now();

            this.vadInterval = setInterval(() => {
                if (!this.isRecording) {
                    this.stopVoiceActivityDetection();
                    return;
                }

                analyser.getByteFrequencyData(dataArray);
                let sum = 0;
                for (let i = 0; i < bufferLength; i++) {
                    sum += dataArray[i];
                }
                const avgVolume = sum / bufferLength;

                // Calibrate ambient noise floor for the first 350ms
                if (Date.now() - calibrationStartTime < 350) {
                    noiseFloorSum += avgVolume;
                    noiseFloorSamples++;
                    ambientNoiseFloor = noiseFloorSum / Math.max(1, noiseFloorSamples);
                }

                const speechThreshold = Math.max(9, ambientNoiseFloor + 5);
                const silenceThreshold = Math.max(6, ambientNoiseFloor + 2.5);

                // Animate equalizer bars dynamically in real time
                if (this.elements.soundWave) {
                    const spans = this.elements.soundWave.querySelectorAll('span');
                    spans.forEach((span, idx) => {
                        const freqIdx = Math.min(bufferLength - 1, Math.floor((idx / spans.length) * (bufferLength / 2)));
                        const val = dataArray[freqIdx] || avgVolume;
                        const scale = Math.max(0.25, Math.min(2.4, (val / 45)));
                        span.style.transform = `scaleY(${scale})`;
                    });
                }

                if (avgVolume > speechThreshold || (this.recognizedTranscript && this.recognizedTranscript.length > 0)) {
                    userStartedSpeaking = true;
                    silenceStartTime = null; // Reset silence timer while speech is active
                    if (this.recognizedTranscript) {
                        this.setStatus(`Listening: <em>"${escapeHtml(this.recognizedTranscript)}"</em>`, 'recording');
                    } else {
                        this.setStatus('Speaking detected ⚡ (auto-stops when you pause)', 'recording');
                    }
                } else if (userStartedSpeaking && avgVolume <= silenceThreshold) {
                    if (!silenceStartTime) {
                        silenceStartTime = Date.now();
                    } else {
                        const elapsedSilence = Date.now() - silenceStartTime;
                        if (elapsedSilence >= 500) {
                            this.setStatus('Silence detected... auto-completing', 'recording');
                        }
                        if (elapsedSilence >= 1500) {
                            console.log('Auto-stopping: Silence detected after speech (1.5s).');
                            this.stopVoiceActivityDetection();
                            this.stopRecording();
                        }
                    }
                }
            }, 80);

        } catch (err) {
            console.warn('Could not initialize AudioContext for VAD:', err);
        }
    },

    stopVoiceActivityDetection() {
        if (this.vadInterval) {
            clearInterval(this.vadInterval);
            this.vadInterval = null;
        }
        if (this.audioContext && this.audioContext.state !== 'closed') {
            try {
                this.audioContext.close();
            } catch (e) {}
            this.audioContext = null;
        }
    },

    /**
     * Stop active recording
     */
    stopRecording() {
        if (!this.isRecording || !this.mediaRecorder) return;

        this.stopVoiceActivityDetection();
        this.stopTimer();
        this.isRecording = false;

        // Visual transition
        this.setStatus('Processing your voice...', 'processing');
        this.elements.card.classList.remove('recording');

        // Stop speech recognizer
        if (this.speechRecognizer) {
            try {
                this.speechRecognizer.stop();
            } catch (e) {}
            this.speechRecognizer = null;
        }

        // Request stop on MediaRecorder
        if (this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }

        // Release hardware audio tracks
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
            this.audioStream = null;
        }
    },

    /**
     * Handle finished audio data after recording stops
     */
    async handleRecordingComplete(mimeType) {
        // Enforce minimum duration (1 second) to reject accidental micro-clicks
        if (this.recordingDurationSeconds < 1) {
            showToast('Recording was too short. Please speak your task clearly.', 'error');
            this.setStatus('Tap to speak', 'idle');
            this.resetTimerDisplay();
            return;
        }

        // Package chunks into a single binary Blob
        const finalMime = mimeType || 'audio/webm';
        const audioBlob = new Blob(this.audioChunks, { type: finalMime });

        if (audioBlob.size === 0) {
            showToast('Audio recording is empty (0 bytes). Please try again.', 'error');
            this.setStatus('Tap to speak', 'idle');
            this.resetTimerDisplay();
            return;
        }

        console.log(`Audio recorded: ${audioBlob.size} bytes (${finalMime}), transcript: "${this.recognizedTranscript}"`);

        // Enter processing pipeline with genuine captured transcript
        await this.processRecordedAudio(audioBlob, this.recognizedTranscript);
    },

    /**
     * Send recorded audio to backend API and handle UI state transitions
     */
    async processRecordedAudio(audioBlob, clientTranscript = '') {
        this.isProcessing = true;
        this.setProcessingUI(true);

        try {
            // Step 1: Uploading
            this.setStatus('<span class="processing-spinner"></span> Transcribing & understanding task...', 'processing');

            // Step 2: Transcribing & Parsing via REST API
            const langSelect = document.getElementById('pref-speech-language');
            const chosenLang = langSelect ? langSelect.value : 'auto';
            const result = await Api.transcribeAudio(audioBlob, clientTranscript, chosenLang);

            if (result && result.success && result.data) {
                this.setStatus('Task detected!', 'success');
                showToast('Speech recognized and task structured!', 'success');

                // Trigger Human-in-the-Loop Confirmation Preview in dashboard
                if (typeof showTaskPreview === 'function') {
                    showTaskPreview(result.data);
                }
            } else {
                throw new Error(result.message || 'Unable to recognize task from audio.');
            }


        } catch (error) {
            console.error('Audio processing failed:', error);
            const errorMsg = error.message || 'Speech recognition failed. Please try again.';
            showToast(errorMsg, 'error', 4500);
            this.setStatus('Tap to speak', 'idle');
        } finally {
            this.isProcessing = false;
            this.setProcessingUI(false);
            this.resetTimerDisplay();
        }
    },

    /**
     * Real-time Recording Timer
     */
    startTimer() {
        this.recordingDurationSeconds = 0;
        this.elements.timerText.textContent = '00:00';

        this.recordingTimerInterval = setInterval(() => {
            const elapsedMs = Date.now() - this.recordingStartTime;
            this.recordingDurationSeconds = Math.floor(elapsedMs / 1000);

            const minutes = String(Math.floor(this.recordingDurationSeconds / 60)).padStart(2, '0');
            const seconds = String(this.recordingDurationSeconds % 60).padStart(2, '0');
            this.elements.timerText.textContent = `${minutes}:${seconds}`;

            // Safety limit check
            if (this.recordingDurationSeconds >= this.maxDurationSeconds) {
                showToast('Maximum recording duration reached (60s). Stopping...', 'info');
                this.stopRecording();
            }
        }, 500);
    },

    stopTimer() {
        if (this.recordingTimerInterval) {
            clearInterval(this.recordingTimerInterval);
            this.recordingTimerInterval = null;
        }
    },

    resetTimerDisplay() {
        this.elements.timerText.textContent = '00:00';
    },

    /**
     * UI Status Label Helper
     */
    setStatus(htmlText, state) {
        if (this.elements.statusText) {
            this.elements.statusText.innerHTML = htmlText;
        }
    },

    /**
     * Disable/Enable button during network upload & AI processing
     */
    setProcessingUI(isProcessing) {
        if (this.elements.toggleBtn) {
            this.elements.toggleBtn.disabled = isProcessing;
            if (isProcessing) {
                this.elements.toggleBtn.style.opacity = '0.6';
                this.elements.toggleBtn.style.cursor = 'wait';
            } else {
                this.elements.toggleBtn.style.opacity = '1';
                this.elements.toggleBtn.style.cursor = 'pointer';
                this.setStatus('Tap to speak', 'idle');
            }
        }
    },

    /**
     * Friendly error messages for microphone hardware/permission failures
     */
    handleMicrophoneError(error) {
        this.isRecording = false;
        this.elements.card.classList.remove('recording');
        this.resetTimerDisplay();

        let message = 'Could not access microphone.';

        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
            message = 'Microphone permission was denied. Please allow microphone access in your browser.';
        } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
            message = 'No microphone was detected on this device.';
        } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
            message = 'Microphone is already in use by another application.';
        } else if (error.name === 'SecurityError') {
            message = 'Microphone access requires HTTPS or localhost.';
        }

        showToast(message, 'error', 5000);
        this.setStatus('Microphone unavailable', 'error');
    }
};

// Auto-initialize recorder when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    VoiceRecorder.init();
});
