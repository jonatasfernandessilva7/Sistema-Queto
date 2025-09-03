let recorder;
let audioStream;
let intervalID;
let consentAccepted = false;

const startButton = document.getElementById('startBtn');
const stopButton = document.getElementById('stopBtn');
const result = document.getElementById('result');
const audioScreen = document.getElementById('audioScreen');
const docsScreen = document.getElementById('docsScreen');
const feedbackScreen = document.getElementById('feedbackScreen');
const consentScreen = document.getElementById('consentScreen');

// Início da gravação
startButton.addEventListener('click', async function () {
  if (!consentAccepted) {
    alert("Você precisa aceitar o termo de consentimento antes de iniciar a gravação.");
    return;
  }

  result.textContent = 'Gravando...';
  audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const audioContext = new (window.AudioContext || window.webkitAudioContext)();
  const input = audioContext.createMediaStreamSource(audioStream);
  recorder = new Recorder(input, { numChannels: 2 });
  recorder.record();

  intervalID = setInterval(() => {
    sendChunkAudio();
  }, 15000);

  startButton.disabled = true;
  stopButton.disabled = false;
});

// Parar gravação
stopButton.addEventListener('click', function () {
  if (!recorder) return;

  recorder.stop();
  audioStream.getTracks().forEach(track => track.stop());

  sendChunkAudio();

  clearInterval(intervalID);

  startButton.disabled = false;
  stopButton.disabled = true;
});

// Envio de áudio para backend
async function sendChunkAudio() {
  recorder.exportWAV(async function (blob) {
    result.textContent = 'Processando áudio...';
    const audio_file = new File([blob], 'gravacao.wav', { type: 'audio/wav' });
    const formData = new FormData();
    formData.append('audio_file', audio_file);

    try {
      startButton.disabled = true;
      const response = await fetch('http://localhost:8080/v1/u/process-audio', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();
      result.textContent = JSON.stringify(data.message, null, 2);
    } catch (err) {
      result.textContent = 'Erro ao enviar áudio. ' + err;
    }

    recorder.clear();
  });
}

// Alternar telas
function showScreen(screen) {
  if (screen === 'audio' && !consentAccepted) {
    alert('Você precisa aceitar o termo de consentimento antes de iniciar a gravação');
    return;
  }

  consentScreen.style.display = (screen === 'consent') ? 'block' : 'none';
  audioScreen.style.display = (screen === 'audio') ? 'block' : 'none';
  docsScreen.style.display = (screen === 'docs') ? 'block' : 'none';
  feedbackScreen.style.display = (screen === 'feedback') ? 'block' : 'none';

  if (screen === 'docs') fetchDocs();
}

// Buscar documentos
async function fetchDocs() {
  const list = document.getElementById('docsList');
  list.innerHTML = 'Carregando...';
  try {
    const response = await fetch('http://localhost:8080/v1/u/docs');
    const docs = await response.json();
    list.innerHTML = '';

    docs.forEach(doc => {
      const li = document.createElement('li');
      li.id = `${doc.id}`;

      const nameSpan = document.createElement('span');
      nameSpan.textContent = `${doc.filename || 'Sem nome'}`;
      li.appendChild(nameSpan);

      const viewBtn = document.createElement('button');
      viewBtn.innerHTML = '&#128065;';
      viewBtn.title = 'Visualizar documento';
      viewBtn.onclick = () => {
        window.open(`http://localhost:8080/v1/u/docs/${doc.id}`, '_blank');
      };
      li.appendChild(viewBtn);

      const delBtn = document.createElement('button');
      delBtn.textContent = 'Deletar';
      delBtn.onclick = async () => {
        if (confirm('Deseja realmente deletar este documento?')) {
          await deleteDoc(doc.id);
        }
      };
      li.appendChild(delBtn);

      list.appendChild(li);
    });

    document.getElementById('uploadDocBtn').onclick = function () {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = '.pdf,.doc,.docx,.txt';
      input.onchange = async function (e) {
        const file = e.target.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);

        list.innerHTML = 'Enviando...';
        try {
          const response = await fetch('http://localhost:8080/v1/u/docs', {
            method: 'POST',
            body: formData
          });
          if (response.ok) {
            showModalBar('Documento enviado com sucesso!');
            fetchDocs();
          } else {
            showModalBar('Erro ao enviar documento.');
            list.innerHTML = 'Erro ao enviar documento.';
          }
        } catch (err) {
          list.innerHTML = 'Erro ao enviar documento. ' + err;
        }
      };
      input.click();
    };
  } catch (err) {
    list.innerHTML = 'Erro ao buscar documentos.';
  }
}

// Deletar documento
async function deleteDoc(docId) {
  const list = document.getElementById('docsList');
  list.innerHTML = 'Deletando...';
  try {
    const response = await fetch(`http://localhost:8080/v1/u/docs/${docId}`, {
      method: 'DELETE',
    });
    if (response.ok) {
      showModalBar('Documento apagado com sucesso!');
      fetchDocs();
    } else {
      showModalBar('Erro ao apagar documento.');
      list.innerHTML = 'Erro ao deletar documento.';
    }
  } catch (err) {
    showModalBar('Erro ao apagar documento.');
    list.innerHTML = 'Erro ao deletar documento.';
  }
}

// Mensagem temporária
function showModalBar(msg) {
  const modal = document.getElementById('modalBar');
  if (!modal) return;
  modal.textContent = msg;
  modal.style.display = 'block';
  setTimeout(() => {
    modal.style.display = 'none';
  }, 2000);
}

// Enviar feedback
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
    await response.json();
    result.textContent = 'Feedback enviado!';
  } catch (err) {
    result.textContent = 'Erro ao enviar feedback.';
  }
}

// Consentimento
async function acceptConsent() {
  const check = document.getElementById("consentCheckbox").checked;
  if (!check) {
    alert("Você precisa marcar a opção antes de confirmar.");
    return;
  }

  consentAccepted = true;
  document.getElementById("consentResult").innerText =
    "✔ Consentimento registrado em " + new Date().toLocaleString();

  const consentData = {
    accepted: true,
    date: new Date().toISOString(),
    version: "1.0"
  };

  // salvar localmente
  localStorage.setItem("consent", JSON.stringify(consentData));

  // salvar via Electron (IPC)
  if (window.electronAPI && window.electronAPI.saveConsent) {
    await window.electronAPI.saveConsent(consentData);
  }
}

// Verificar consentimento salvo
window.onload = () => {
  const saved = localStorage.getItem("consent");
  if (saved) {
    const data = JSON.parse(saved);
    consentAccepted = data.accepted;
    document.getElementById("consentResult").innerText =
      "Já aceito em " + new Date(data.date).toLocaleString();
  }
};

window.showScreen = showScreen;
window.sendFeedback = sendFeedback;
window.acceptConsent = acceptConsent;