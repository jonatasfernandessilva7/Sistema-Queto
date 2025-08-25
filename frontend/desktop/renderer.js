const axios = require('axios');

let recorder;
let audioStream;

document.getElementById('startBtn').onclick = async function () {
  document.getElementById('result').textContent = 'Gravando...';
  audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const audioContext = new (window.AudioContext || window.webkitAudioContext)();
  const input = audioContext.createMediaStreamSource(audioStream);
  recorder = new Recorder(input, { numChannels: 2 });
  recorder.record();
  document.getElementById('startBtn').disabled = true;
  document.getElementById('stopBtn').disabled = false;
};

document.getElementById('stopBtn').onclick = function () {
  recorder.stop();
  audioStream.getTracks().forEach(track => track.stop());
  recorder.exportWAV(async function (blob) {
    document.getElementById('result').textContent = 'Processando áudio...';
    const audio_file = new File([blob], 'gravacao.wav', { type: 'audio/wav' });
    const formData = new FormData();
    formData.append('audio_file', audio_file);

    try {
      const response = await axios.post('http://localhost:8080/v1/u/process-audio', formData, {
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

function showScreen(screen) {
  document.getElementById('audioScreen').style.display = (screen === 'audio') ? 'block' : 'none';
  document.getElementById('docsScreen').style.display = (screen === 'docs') ? 'block' : 'none';
  document.getElementById('feedbackScreen').style.display = (screen === 'feedback') ? 'block' : 'none';
  if (screen == 'docs') fetchDocs();
}

async function fetchDocs() {
  const list = document.getElementById('docsList');
  list.innerHTML = 'Carregando...';
  try {
    const response = await fetch('http://localhost:8080/v1/u/docs');
    const docs = await response.json();
    list.innerHTML = '';
    docs.forEach(doc => {
      const li = document.createElement('li');
      li.id = `${doc.id}`
      li.textContent = `${doc.filename || 'Sem nome'}`;
      const delBtn = document.createElement('button');
      delBtn.textContent = 'Deletar';
      delBtn.style.marginLeft = '12px';
      delBtn.onclick = async () => {
        if (confirm('Deseja realmente deletar este documento?')) {
          await deleteDoc(doc.id);
        }
      };
      li.appendChild(delBtn);
      list.appendChild(li);
    });
  } catch (err) {
    list.innerHTML = 'Erro ao buscar documentos.';
  }
}

async function deleteDoc(docId) {
  const list = document.getElementById('docsList');
  list.innerHTML = 'Deletando...';
  try {
    const response = await fetch(`http://localhost:8080/v1/u/docs/${docId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    if (response.ok) {
      fetchDocs(); // Atualiza lista após deletar
    } else {
      list.innerHTML = 'Erro ao deletar documento.';
    }
  } catch (err) {
    list.innerHTML = 'Erro ao deletar documento.';
  }
}

async function sendFeedback(event) {
  event.preventDefault();
  const text = document.getElementById('feedbackText').value;
  const result = document.getElementById('feedbackResult');
  result.textContent = 'Enviando...';
  try {
    const response = await fetch('http://localhost:8080/v1/u/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ feedback: text })
    });
    const data = await response.json();
    result.textContent = 'Feedback enviado!';
  } catch (err) {
    result.textContent = 'Erro ao enviar feedback.';
  }
}