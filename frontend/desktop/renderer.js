const axios = require('axios');

let recorder;
let audioStream;

document.getElementById('startBtn').onclick = async function() {
  document.getElementById('result').textContent = 'Gravando...';
  audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const audioContext = new (window.AudioContext || window.webkitAudioContext)();
  const input = audioContext.createMediaStreamSource(audioStream);
  recorder = new Recorder(input, { numChannels: 2 });
  recorder.record();
  document.getElementById('startBtn').disabled = true;
  document.getElementById('stopBtn').disabled = false;
};

document.getElementById('stopBtn').onclick = function() {
  recorder.stop();
  audioStream.getTracks().forEach(track => track.stop());
  recorder.exportWAV(async function(blob) {
    document.getElementById('result').textContent = 'Processando áudio...';
    const audio_file = new File([blob], 'gravacao.wav', { type: 'audio/wav' });
    const formData = new FormData();
    formData.append('audio_file', audio_file);

    try {
        const response = await axios.post('http://localhost:3000/v1/u/process-audio', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        document.getElementById('result').textContent = JSON.stringify(response.data.message, null, 2);
    } catch (err) {
        document.getElementById('result').textContent = 'Erro ao enviar áudio.' + err;
    }
  });
  document.getElementById('startBtn').disabled = false;
  document.getElementById('stopBtn').disabled = true;
};