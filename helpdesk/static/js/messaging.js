/* ═══════════════════════════════════════════════════════════════════
   MESSAGING JS — Real-time chat, file upload, voice, WebRTC calls
   ═══════════════════════════════════════════════════════════════════ */

(function() {
'use strict';

// ── Config ──────────────────────────────────────────────────────────
const POLL_INTERVAL = 2000;       // Poll messages every 2s
const CONV_POLL_INTERVAL = 5000;  // Poll conversation list every 5s
const TYPING_TIMEOUT = 3000;

// ── DOM Elements ────────────────────────────────────────────────────
const conversationId = document.getElementById('conversationId')?.value;
const currentUserId = document.getElementById('currentUserId')?.value;
const csrfToken = document.getElementById('csrfToken')?.value;
const messagesContainer = document.getElementById('messagesContainer');
const messageInput = document.getElementById('messageInput');
const btnSend = document.getElementById('btnSend');
const fileInput = document.getElementById('fileInput');
const imageInput = document.getElementById('imageInput');
const filePreview = document.getElementById('filePreview');
const filePreviewName = document.getElementById('filePreviewName');
const btnCancelFile = document.getElementById('btnCancelFile');
const btnVoiceRecord = document.getElementById('btnVoiceRecord');
const typingIndicator = document.getElementById('typingIndicator');
const btnNewChat = document.getElementById('btnNewChat');
const btnCreateGroup = document.getElementById('btnCreateGroup');
const searchConversations = document.getElementById('searchConversations');
const btnBackToList = document.getElementById('btnBackToList');

let lastMessageId = 0;
let selectedFile = null;
let typingTimer = null;
let isTyping = false;
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

// ── Initialize ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  initializeMessaging();
  initializeModals();
  initializeSearch();
  initializeMobileNav();
  initializePolling();
  initializeCallUI();
  pollIncomingCalls();
});

function initializeMessaging() {
  if (!conversationId) return;

  // Scroll to bottom
  scrollToBottom();

  // Get last message ID
  const msgs = messagesContainer?.querySelectorAll('.msg-bubble');
  if (msgs && msgs.length > 0) {
    lastMessageId = msgs[msgs.length - 1].dataset.id || 0;
  }

  // Send button
  btnSend?.addEventListener('click', sendMessage);

  // Enter to send
  messageInput?.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Auto-resize textarea
  messageInput?.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    handleTyping();
  });

  // File inputs
  fileInput?.addEventListener('change', handleFileSelect);
  imageInput?.addEventListener('change', handleFileSelect);
  btnCancelFile?.addEventListener('click', cancelFileSelect);

  // Voice recording
  btnVoiceRecord?.addEventListener('click', toggleVoiceRecording);
}

// ── Send Message ────────────────────────────────────────────────────
function sendMessage() {
  const content = messageInput?.value.trim();
  if (!content && !selectedFile) return;

  const formData = new FormData();
  formData.append('conversation_id', conversationId);
  formData.append('content', content || '');

  if (selectedFile) {
    formData.append('file', selectedFile);
    const name = selectedFile.name.toLowerCase();
    if (name.match(/\.(png|jpg|jpeg|gif|webp)$/)) {
      formData.append('message_type', 'image');
    } else if (name.match(/\.(ogg|webm|mp3|wav|m4a)$/)) {
      formData.append('message_type', 'voice');
    } else {
      formData.append('message_type', 'file');
    }
  } else {
    formData.append('message_type', 'text');
  }

  fetch('/messages/api/send/', {
    method: 'POST',
    headers: { 'X-CSRFToken': csrfToken },
    body: formData
  })
  .then(r => r.json())
  .then(data => {
    if (data.status === 'ok') {
      appendMessage(data.message, true);
      messageInput.value = '';
      messageInput.style.height = 'auto';
      cancelFileSelect();
      scrollToBottom();
      stopTyping();
    }
  })
  .catch(err => console.error('Send error:', err));
}

// ── Append Message to DOM ───────────────────────────────────────────
function appendMessage(msg, isSent) {
  if (!messagesContainer) return;

  const isMine = String(msg.sender_id) === String(currentUserId);

  // Call message (centered)
  if (msg.message_type === 'call') {
    const callDiv = document.createElement('div');
    callDiv.className = 'msg-call-event';
    callDiv.dataset.id = msg.id;
    const callLog = msg.call_log || {};
    const isDeclined = callLog.status === 'rejected' || callLog.status === 'missed';
    const icon = callLog.call_type === 'video' ? 'fa-video' : 'fa-phone';
    let label = 'Call';
    if (callLog.status === 'ended') label = callLog.call_type === 'video' ? 'Video call' : 'Voice call';
    else if (callLog.status === 'rejected') label = 'Declined call';
    else if (callLog.status === 'missed') label = 'Missed call';

    callDiv.innerHTML = `
      <div class="msg-call-bubble">
        <div class="msg-call-icon ${isDeclined ? 'declined' : ''}"><i class="fa ${icon}"></i></div>
        <div class="msg-call-info">
          <span class="msg-call-label">${label}</span>
          <span class="msg-call-time">
            ${isDeclined ? '<i class="fa fa-arrow-down" style="color:#e17055;font-size:0.7rem;"></i>' : '<i class="fa fa-arrow-up" style="color:#00b894;font-size:0.7rem;"></i>'}
            ${msg.created_at}
          </span>
        </div>
        <button class="msg-call-action" onclick="initiateCall('${callLog.call_type || 'voice'}')"><i class="fa ${icon}"></i></button>
      </div>`;
    messagesContainer.appendChild(callDiv);
    lastMessageId = msg.id;
    return;
  }

  // Deleted message
  if (msg.is_deleted) {
    const bubble = document.createElement('div');
    bubble.className = `msg-bubble ${isMine ? 'sent' : 'received'} deleted`;
    bubble.dataset.id = msg.id;
    bubble.innerHTML = `<div class="msg-content"><div class="msg-text deleted-text"><i class="fa fa-ban"></i> This message was deleted</div><div class="msg-time">${msg.created_at}</div></div>`;
    messagesContainer.appendChild(bubble);
    lastMessageId = msg.id;
    return;
  }

  const bubble = document.createElement('div');
  bubble.className = `msg-bubble ${isMine ? 'sent' : 'received'}`;
  bubble.dataset.id = msg.id;

  let avatarHtml = '';
  if (!isMine) {
    if (msg.profile_picture) {
      avatarHtml = `<div class="msg-avatar-small"><img src="${msg.profile_picture}" alt=""></div>`;
    } else {
      avatarHtml = `<div class="msg-avatar-small"><div class="avatar-initials tiny">${msg.sender.charAt(0).toUpperCase()}</div></div>`;
    }
  }

  let contentHtml = '';
  if (msg.message_type === 'image' && msg.file_url) {
    contentHtml += `<div class="msg-image"><img src="${msg.file_url}" alt="Image" onclick="openImageModal(this.src)"></div>`;
  } else if (msg.message_type === 'voice' && msg.file_url) {
    contentHtml += `<div class="msg-voice"><audio controls preload="auto"><source src="${msg.file_url}" type="audio/webm"><source src="${msg.file_url}" type="video/webm"></audio></div>`;
  } else if (msg.message_type === 'file' && msg.file_url) {
    contentHtml += `<div class="msg-file"><a href="${msg.file_url}" target="_blank"><i class="fa fa-file"></i> File</a></div>`;
  }

  if (msg.content) {
    contentHtml += `<div class="msg-text">${escapeHtml(msg.content)}</div>`;
  }

  const editedTag = msg.is_edited ? '<span class="msg-edited">edited</span>' : '';
  contentHtml += `<div class="msg-time">${editedTag}${msg.created_at}${isMine ? ' <i class="fa fa-check-double"></i>' : ''}</div>`;

  let actionsHtml = '';
  if (isMine) {
    actionsHtml = `<div class="msg-actions-trigger" onclick="showMessageMenu(event, ${msg.id}, '${msg.message_type}')"><i class="fa fa-ellipsis-v"></i></div>`;
  }

  bubble.innerHTML = `${avatarHtml}<div class="msg-content">${contentHtml}</div>${actionsHtml}`;
  messagesContainer.appendChild(bubble);

  lastMessageId = msg.id;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function scrollToBottom() {
  if (messagesContainer) {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
}

// ── File Handling ───────────────────────────────────────────────────
function handleFileSelect(e) {
  const file = e.target.files[0];
  if (!file) return;
  selectedFile = file;
  filePreviewName.textContent = file.name;
  filePreview.style.display = 'flex';
}

function cancelFileSelect() {
  selectedFile = null;
  if (filePreview) filePreview.style.display = 'none';
  if (fileInput) fileInput.value = '';
  if (imageInput) imageInput.value = '';
}

// ── Voice Recording ─────────────────────────────────────────────────
function toggleVoiceRecording() {
  if (isRecording) {
    // If already recording, pause/resume
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.pause();
      pauseRecordingUI();
    } else if (mediaRecorder && mediaRecorder.state === 'paused') {
      mediaRecorder.resume();
      resumeRecordingUI();
    }
  } else {
    startRecording();
  }
}

let recordingSeconds = 0;
let recordingTimer = null;
let recordingStream = null;

function startRecording() {
  navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } })
    .then(stream => {
      recordingStream = stream;
      const mimeType = getSupportedMimeType();
      mediaRecorder = new MediaRecorder(stream, { mimeType: mimeType, audioBitsPerSecond: 128000 });
      audioChunks = [];

      mediaRecorder.ondataavailable = e => {
        if (e.data && e.data.size > 0) {
          audioChunks.push(e.data);
        }
      };

      // Start recording WITHOUT timeslice — data is collected on stop/requestData
      mediaRecorder.start();
      isRecording = true;
      recordingSeconds = 0;
      showVoiceRecorderPopup();
      startRecordingTimer();
    })
    .catch(err => {
      console.error('Mic error:', err);
      alert('Cannot access microphone. Please allow microphone permission.');
    });
}

function getSupportedMimeType() {
  const types = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/mp4'
  ];
  for (const type of types) {
    if (MediaRecorder.isTypeSupported(type)) return type;
  }
  return '';
}

function finishRecording() {
  return new Promise(resolve => {
    if (!mediaRecorder || mediaRecorder.state === 'inactive') {
      resolve();
      return;
    }
    mediaRecorder.ondataavailable = e => {
      if (e.data && e.data.size > 0) {
        audioChunks.push(e.data);
      }
    };
    mediaRecorder.onstop = () => {
      resolve();
    };
    mediaRecorder.stop();
  });
}

function stopRecordingStream() {
  if (recordingStream) {
    recordingStream.getTracks().forEach(t => t.stop());
    recordingStream = null;
  }
  isRecording = false;
  stopRecordingTimer();
}

function cancelRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }
  stopRecordingStream();
  audioChunks = [];
  hideVoiceRecorderPopup();
}

function sendRecording() {
  finishRecording().then(() => {
    stopRecordingStream();

    if (audioChunks.length === 0) {
      hideVoiceRecorderPopup();
      return;
    }

    const mimeType = getSupportedMimeType() || 'audio/webm';
    const ext = mimeType.includes('ogg') ? 'ogg' : mimeType.includes('mp4') ? 'mp4' : 'webm';
    const audioBlob = new Blob(audioChunks, { type: mimeType });

    // Verify the blob has actual content
    if (audioBlob.size < 100) {
      alert('Recording too short. Please try again.');
      hideVoiceRecorderPopup();
      return;
    }

    const file = new File([audioBlob], `voice_${Date.now()}.${ext}`, { type: mimeType });
    sendVoiceMessage(file);
    hideVoiceRecorderPopup();
  });
}

function startRecordingTimer() {
  recordingTimer = setInterval(() => {
    recordingSeconds++;
    updateRecordingTimerUI();
  }, 1000);
}

function stopRecordingTimer() {
  if (recordingTimer) {
    clearInterval(recordingTimer);
    recordingTimer = null;
  }
}

function updateRecordingTimerUI() {
  const el = document.getElementById('voiceRecordTime');
  if (el) {
    const mins = String(Math.floor(recordingSeconds / 60)).padStart(2, '0');
    const secs = String(recordingSeconds % 60).padStart(2, '0');
    el.textContent = `${mins}:${secs}`;
  }
}

function pauseRecordingUI() {
  const pauseBtn = document.getElementById('voicePauseBtn');
  if (pauseBtn) pauseBtn.innerHTML = '<i class="fa fa-play"></i>';
  stopRecordingTimer();
}

function resumeRecordingUI() {
  const pauseBtn = document.getElementById('voicePauseBtn');
  if (pauseBtn) pauseBtn.innerHTML = '<i class="fa fa-pause"></i>';
  startRecordingTimer();
}

function showVoiceRecorderPopup() {
  let popup = document.getElementById('voiceRecorderPopup');
  if (!popup) {
    popup = document.createElement('div');
    popup.id = 'voiceRecorderPopup';
    popup.className = 'voice-recorder-popup';
    popup.innerHTML = `
      <button class="voice-rec-btn delete" id="voiceDeleteBtn" title="Cancel">
        <i class="fa fa-trash"></i>
      </button>
      <div class="voice-rec-body">
        <button class="voice-rec-btn pause" id="voicePauseBtn" title="Pause/Resume">
          <i class="fa fa-pause"></i>
        </button>
        <div class="voice-rec-wave">
          <span></span><span></span><span></span><span></span><span></span><span></span>
        </div>
        <span class="voice-rec-time" id="voiceRecordTime">00:00</span>
      </div>
      <button class="voice-rec-btn send" id="voiceSendBtn" title="Send">
        <i class="fa fa-paper-plane"></i>
      </button>
    `;
    document.querySelector('.msg-input-area').appendChild(popup);

    document.getElementById('voiceDeleteBtn').addEventListener('click', cancelRecording);
    document.getElementById('voiceSendBtn').addEventListener('click', sendRecording);
    document.getElementById('voicePauseBtn').addEventListener('click', toggleVoiceRecording);
  }
  popup.style.display = 'flex';
  document.getElementById('voiceRecordTime').textContent = '00:00';
  const pauseBtn = document.getElementById('voicePauseBtn');
  if (pauseBtn) pauseBtn.innerHTML = '<i class="fa fa-pause"></i>';
  // Hide normal input row
  document.querySelector('.msg-input-row').style.display = 'none';
}

function hideVoiceRecorderPopup() {
  const popup = document.getElementById('voiceRecorderPopup');
  if (popup) popup.style.display = 'none';
  // Show normal input row
  const inputRow = document.querySelector('.msg-input-row');
  if (inputRow) inputRow.style.display = 'flex';
}

function sendVoiceMessage(file) {
  const formData = new FormData();
  formData.append('conversation_id', conversationId);
  formData.append('content', '');
  formData.append('message_type', 'voice');
  formData.append('file', file);

  fetch('/messages/api/send/', {
    method: 'POST',
    headers: { 'X-CSRFToken': csrfToken },
    body: formData
  })
  .then(r => r.json())
  .then(data => {
    if (data.status === 'ok') {
      appendMessage(data.message, true);
      scrollToBottom();
    }
  });
}

// ── Typing Indicator ────────────────────────────────────────────────
function handleTyping() {
  if (!isTyping) {
    isTyping = true;
    sendTypingStatus(true);
  }
  clearTimeout(typingTimer);
  typingTimer = setTimeout(stopTyping, TYPING_TIMEOUT);
}

function stopTyping() {
  if (isTyping) {
    isTyping = false;
    sendTypingStatus(false);
  }
}

function sendTypingStatus(typing) {
  if (!conversationId) return;
  fetch('/messages/api/typing/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      is_typing: typing
    })
  }).catch(() => {});
}

// ── Polling ─────────────────────────────────────────────────────────
function initializePolling() {
  if (conversationId) {
    setInterval(pollNewMessages, POLL_INTERVAL);
  }
  setInterval(pollConversations, CONV_POLL_INTERVAL);
}

function pollNewMessages() {
  if (!conversationId) return;
  fetch(`/messages/api/messages/${conversationId}/?after=${lastMessageId}`)
    .then(r => r.json())
    .then(data => {
      if (data.messages && data.messages.length > 0) {
        data.messages.forEach(msg => {
          // Don't duplicate
          if (!document.querySelector(`.msg-bubble[data-id="${msg.id}"]`)) {
            appendMessage(msg, false);
          }
        });
        scrollToBottom();
      }
    })
    .catch(() => {});
}

function pollConversations() {
  fetch('/messages/api/conversations/')
    .then(r => r.json())
    .then(data => {
      if (data.conversations) {
        updateConversationList(data.conversations);
        updateTypingFromConversations(data.conversations);
      }
    })
    .catch(() => {});
}

function updateConversationList(conversations) {
  const list = document.getElementById('conversationList');
  if (!list) return;

  conversations.forEach(conv => {
    const item = list.querySelector(`[data-id="${conv.id}"]`);
    if (item) {
      // Update unread badge
      const badge = item.querySelector('.msg-unread-badge');
      if (conv.unread_count > 0) {
        if (badge) {
          badge.textContent = conv.unread_count;
        } else {
          const bottom = item.querySelector('.msg-conv-bottom');
          if (bottom) {
            bottom.insertAdjacentHTML('beforeend',
              `<span class="msg-unread-badge">${conv.unread_count}</span>`);
          }
        }
      } else if (badge) {
        badge.remove();
      }

      // Update preview
      const preview = item.querySelector('.msg-conv-preview');
      if (preview && conv.last_message) {
        let previewText = conv.last_message.content;
        if (conv.last_message.type === 'image') previewText = '📷 Photo';
        else if (conv.last_message.type === 'voice') previewText = '🎤 Voice';
        else if (conv.last_message.type === 'file') previewText = '📎 File';
        preview.textContent = previewText?.substring(0, 35) || '';
      }
    }
  });
}

function updateTypingFromConversations(conversations) {
  if (!conversationId || !typingIndicator) return;
  const current = conversations.find(c => String(c.id) === String(conversationId));
  if (current && current.typing_users && current.typing_users.length > 0) {
    typingIndicator.innerHTML = `<span class="typing-dots"><span></span><span></span><span></span></span> ${current.typing_users.join(', ')} typing...`;
  } else {
    // Restore default
    const chatHeader = document.querySelector('.msg-chat-status');
    if (chatHeader && !chatHeader.innerHTML.includes('typing')) return;
  }
}

// ── Modals ──────────────────────────────────────────────────────────
function initializeModals() {
  btnNewChat?.addEventListener('click', () => {
    new bootstrap.Modal(document.getElementById('newChatModal')).show();
  });

  btnCreateGroup?.addEventListener('click', () => {
    new bootstrap.Modal(document.getElementById('createGroupModal')).show();
  });
}

// ── Search ──────────────────────────────────────────────────────────
function initializeSearch() {
  // Search conversations
  searchConversations?.addEventListener('input', function() {
    const val = this.value.toLowerCase();
    document.querySelectorAll('.msg-conv-item').forEach(item => {
      const name = item.querySelector('.msg-conv-name')?.textContent.toLowerCase() || '';
      item.style.display = name.includes(val) ? '' : 'none';
    });
  });

  // Search users in new chat modal
  const searchUsers = document.getElementById('searchUsers');
  searchUsers?.addEventListener('input', function() {
    const val = this.value.toLowerCase();
    document.querySelectorAll('#userList .msg-user-item').forEach(item => {
      const name = (item.dataset.name || '').toLowerCase();
      item.style.display = name.includes(val) ? '' : 'none';
    });
  });

  // Search users in group modal
  const searchGroupMembers = document.getElementById('searchGroupMembers');
  searchGroupMembers?.addEventListener('input', function() {
    const val = this.value.toLowerCase();
    document.querySelectorAll('#groupUserList .msg-user-item').forEach(item => {
      const name = (item.dataset.name || '').toLowerCase();
      item.style.display = name.includes(val) ? '' : 'none';
    });
  });
}

// ── Mobile Navigation ───────────────────────────────────────────────
function initializeMobileNav() {
  const container = document.querySelector('.messaging-container');
  if (conversationId && container) {
    container.classList.add('chat-open');
  }

  btnBackToList?.addEventListener('click', () => {
    container?.classList.remove('chat-open');
  });
}

// ═══════════════════════════════════════════════════════════════════
// WEBRTC CALL SYSTEM
// ═══════════════════════════════════════════════════════════════════

let peerConnection = null;
let localStream = null;
let remoteStream = null;
let currentCallId = null;
let callType = null; // 'voice' or 'video'
let callTimer = null;
let callSeconds = 0;
let callPollInterval = null;

const ICE_SERVERS = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
  ]
};

function initializeCallUI() {
  const btnVoiceCall = document.getElementById('btnVoiceCall');
  const btnVideoCall = document.getElementById('btnVideoCall');
  const btnEndCall = document.getElementById('btnEndCall');
  const btnCancelCall = document.getElementById('btnCancelCall');
  const btnAcceptCall = document.getElementById('btnAcceptCall');
  const btnRejectCall = document.getElementById('btnRejectCall');
  const btnToggleMic = document.getElementById('btnToggleMic');
  const btnToggleCamera = document.getElementById('btnToggleCamera');

  btnVoiceCall?.addEventListener('click', () => initiateCall('voice'));
  btnVideoCall?.addEventListener('click', () => initiateCall('video'));
  btnEndCall?.addEventListener('click', endCall);
  btnCancelCall?.addEventListener('click', endCall);
  btnAcceptCall?.addEventListener('click', acceptCall);
  btnRejectCall?.addEventListener('click', rejectCall);
  btnToggleMic?.addEventListener('click', toggleMic);
  btnToggleCamera?.addEventListener('click', toggleCamera);
}

// ── Initiate Call ───────────────────────────────────────────────────
function initiateCall(type) {
  if (!conversationId) return;
  callType = type;

  fetch('/messages/api/call/initiate/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      call_type: type
    })
  })
  .then(r => r.json())
  .then(data => {
    if (data.status === 'ok') {
      currentCallId = data.call_id;
      showOutgoingCall();
      startCallPolling();
      setupLocalMedia(type);
    }
  })
  .catch(err => console.error('Call initiate error:', err));
}

// ── Accept Call ─────────────────────────────────────────────────────
function acceptCall() {
  if (!currentCallId) return;

  fetch('/messages/api/call/respond/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      call_id: currentCallId,
      action: 'accept'
    })
  })
  .then(r => r.json())
  .then(data => {
    if (data.status === 'ok') {
      showActiveCall();
      setupLocalMedia(callType);
      startCallPolling();
    }
  });
}

// ── Reject Call ─────────────────────────────────────────────────────
function rejectCall() {
  if (!currentCallId) return;

  fetch('/messages/api/call/respond/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      call_id: currentCallId,
      action: 'reject'
    })
  })
  .then(() => {
    hideCallUI();
    cleanupCall();
  });
}

// ── End Call ────────────────────────────────────────────────────────
function endCall() {
  if (!currentCallId) { hideCallUI(); return; }

  fetch('/messages/api/call/respond/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      call_id: currentCallId,
      action: 'end'
    })
  })
  .then(() => {
    hideCallUI();
    cleanupCall();
  });
}

// ── WebRTC Setup ────────────────────────────────────────────────────
async function setupLocalMedia(type) {
  try {
    const constraints = {
      audio: true,
      video: type === 'video'
    };
    localStream = await navigator.mediaDevices.getUserMedia(constraints);

    if (type === 'video') {
      const localVideo = document.getElementById('localVideo');
      if (localVideo) {
        localVideo.srcObject = localStream;
      }
    }

    setupPeerConnection();
  } catch (err) {
    console.error('Media error:', err);
    alert('Cannot access camera/microphone. Please allow permissions.');
    endCall();
  }
}

function setupPeerConnection() {
  peerConnection = new RTCPeerConnection(ICE_SERVERS);

  // Add local tracks
  if (localStream) {
    localStream.getTracks().forEach(track => {
      peerConnection.addTrack(track, localStream);
    });
  }

  // Handle remote stream
  peerConnection.ontrack = (event) => {
    remoteStream = event.streams[0];
    const remoteVideo = document.getElementById('remoteVideo');
    if (remoteVideo) {
      remoteVideo.srcObject = remoteStream;
    }
  };

  // Handle ICE candidates
  peerConnection.onicecandidate = (event) => {
    if (event.candidate) {
      sendSignal('ice-candidate', event.candidate);
    }
  };

  peerConnection.onconnectionstatechange = () => {
    if (peerConnection.connectionState === 'connected') {
      startCallTimer();
    } else if (peerConnection.connectionState === 'disconnected' ||
               peerConnection.connectionState === 'failed') {
      endCall();
    }
  };
}

async function createOffer() {
  if (!peerConnection) return;
  const offer = await peerConnection.createOffer();
  await peerConnection.setLocalDescription(offer);
  sendSignal('offer', offer);
}

async function handleSignal(signal) {
  if (!peerConnection) setupPeerConnection();

  if (signal.type === 'offer') {
    await peerConnection.setRemoteDescription(new RTCSessionDescription(signal.data));
    const answer = await peerConnection.createAnswer();
    await peerConnection.setLocalDescription(answer);
    sendSignal('answer', answer);
  } else if (signal.type === 'answer') {
    await peerConnection.setRemoteDescription(new RTCSessionDescription(signal.data));
  } else if (signal.type === 'ice-candidate') {
    try {
      await peerConnection.addIceCandidate(new RTCIceCandidate(signal.data));
    } catch (err) {
      console.error('ICE candidate error:', err);
    }
  }
}

function sendSignal(type, data) {
  if (!currentCallId) return;
  fetch('/messages/api/call/signal/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      call_id: currentCallId,
      type: type,
      data: data
    })
  }).catch(() => {});
}

// ── Call Polling ────────────────────────────────────────────────────
function startCallPolling() {
  if (callPollInterval) clearInterval(callPollInterval);
  callPollInterval = setInterval(pollCallStatus, 1500);
}

function pollCallStatus() {
  if (!currentCallId) return;

  fetch(`/messages/api/call/status/${currentCallId}/`)
    .then(r => r.json())
    .then(data => {
      // Handle response from other party
      if (data.response === 'accepted') {
        showActiveCall();
        createOffer();
      } else if (data.response === 'rejected' || data.response === 'ended') {
        hideCallUI();
        cleanupCall();
        return;
      }

      // Handle WebRTC signals
      if (data.signals && data.signals.length > 0) {
        data.signals.forEach(signal => handleSignal(signal));
      }
    })
    .catch(() => {});
}

// Poll for incoming calls (runs globally)
function pollIncomingCalls() {
  setInterval(() => {
    // Use a dummy call_id=0 just to check incoming
    fetch('/messages/api/call/status/0/')
      .then(r => r.json())
      .then(data => {
        if (data.incoming_call && !currentCallId) {
          currentCallId = data.incoming_call.call_id;
          callType = data.incoming_call.call_type;
          showIncomingCall(data.incoming_call);
        }
      })
      .catch(() => {});
  }, 3000);
}

// ── Call UI Helpers ──────────────────────────────────────────────────
function showOutgoingCall() {
  document.getElementById('callOverlay').style.display = 'flex';
  document.getElementById('outgoingCallScreen').style.display = 'flex';
  document.getElementById('incomingCallScreen').style.display = 'none';
  document.getElementById('activeCallScreen').style.display = 'none';

  const name = document.querySelector('.msg-chat-name')?.textContent.trim() || 'User';
  document.getElementById('outgoingCallName').textContent = name;
  document.getElementById('outgoingCallAvatar').textContent = name.charAt(0).toUpperCase();
}

function showIncomingCall(callData) {
  document.getElementById('callOverlay').style.display = 'flex';
  document.getElementById('incomingCallScreen').style.display = 'flex';
  document.getElementById('outgoingCallScreen').style.display = 'none';
  document.getElementById('activeCallScreen').style.display = 'none';

  document.getElementById('incomingCallerName').textContent = callData.caller_name;
  document.getElementById('incomingCallType').textContent =
    callData.call_type === 'video' ? 'Video Call' : 'Voice Call';

  const avatar = document.getElementById('incomingCallerAvatar');
  if (callData.caller_avatar) {
    avatar.innerHTML = `<img src="${callData.caller_avatar}" alt="">`;
  } else {
    avatar.textContent = callData.caller_name.charAt(0).toUpperCase();
  }
}

function showActiveCall() {
  document.getElementById('callOverlay').style.display = 'flex';
  document.getElementById('activeCallScreen').style.display = 'flex';
  document.getElementById('outgoingCallScreen').style.display = 'none';
  document.getElementById('incomingCallScreen').style.display = 'none';

  const videoContainer = document.getElementById('callVideoContainer');
  if (callType === 'video' && videoContainer) {
    videoContainer.style.display = 'block';
  }

  const name = document.querySelector('.msg-chat-name')?.textContent.trim() ||
               document.getElementById('incomingCallerName')?.textContent || 'User';
  document.getElementById('activeCallName').textContent = name;
  document.getElementById('activeCallAvatar').textContent = name.charAt(0).toUpperCase();
}

function hideCallUI() {
  document.getElementById('callOverlay').style.display = 'none';
  document.getElementById('outgoingCallScreen').style.display = 'none';
  document.getElementById('incomingCallScreen').style.display = 'none';
  document.getElementById('activeCallScreen').style.display = 'none';
}

// ── Toggle Mic/Camera ───────────────────────────────────────────────
function toggleMic() {
  if (!localStream) return;
  const audioTrack = localStream.getAudioTracks()[0];
  if (audioTrack) {
    audioTrack.enabled = !audioTrack.enabled;
    const btn = document.getElementById('btnToggleMic');
    btn.classList.toggle('muted');
    btn.innerHTML = audioTrack.enabled ?
      '<i class="fa fa-microphone"></i>' :
      '<i class="fa fa-microphone-slash"></i>';
  }
}

function toggleCamera() {
  if (!localStream) return;
  const videoTrack = localStream.getVideoTracks()[0];
  if (videoTrack) {
    videoTrack.enabled = !videoTrack.enabled;
    const btn = document.getElementById('btnToggleCamera');
    btn.classList.toggle('muted');
    btn.innerHTML = videoTrack.enabled ?
      '<i class="fa fa-video"></i>' :
      '<i class="fa fa-video-slash"></i>';
  }
}

// ── Call Timer ───────────────────────────────────────────────────────
function startCallTimer() {
  callSeconds = 0;
  if (callTimer) clearInterval(callTimer);
  callTimer = setInterval(() => {
    callSeconds++;
    const mins = String(Math.floor(callSeconds / 60)).padStart(2, '0');
    const secs = String(callSeconds % 60).padStart(2, '0');
    const el = document.getElementById('callTimer');
    if (el) el.textContent = `${mins}:${secs}`;
  }, 1000);
}

// ── Cleanup ─────────────────────────────────────────────────────────
function cleanupCall() {
  if (peerConnection) {
    peerConnection.close();
    peerConnection = null;
  }
  if (localStream) {
    localStream.getTracks().forEach(t => t.stop());
    localStream = null;
  }
  remoteStream = null;
  currentCallId = null;
  callType = null;
  if (callTimer) { clearInterval(callTimer); callTimer = null; }
  if (callPollInterval) { clearInterval(callPollInterval); callPollInterval = null; }
  callSeconds = 0;
}

// ── Image Modal ─────────────────────────────────────────────────────
window.openImageModal = function(src) {
  document.getElementById('modalImage').src = src;
  new bootstrap.Modal(document.getElementById('imageModal')).show();
};

// ═══════════════════════════════════════════════════════════════════
// EDIT & DELETE MESSAGES
// ═══════════════════════════════════════════════════════════════════

let activeMenuMessageId = null;
let activeMenuType = null;

window.showMessageMenu = function(event, messageId, messageType) {
  event.stopPropagation();
  activeMenuMessageId = messageId;
  activeMenuType = messageType;

  const menu = document.getElementById('msgContextMenu');
  const editBtn = document.getElementById('ctxEditBtn');

  // Only show edit for text messages
  editBtn.style.display = (messageType === 'text') ? 'flex' : 'none';

  menu.style.display = 'block';
  menu.style.left = event.clientX + 'px';
  menu.style.top = event.clientY + 'px';

  // Adjust if menu goes off screen
  const rect = menu.getBoundingClientRect();
  if (rect.right > window.innerWidth) {
    menu.style.left = (event.clientX - rect.width) + 'px';
  }
  if (rect.bottom > window.innerHeight) {
    menu.style.top = (event.clientY - rect.height) + 'px';
  }
};

// Close context menu on click anywhere
document.addEventListener('click', function() {
  const menu = document.getElementById('msgContextMenu');
  if (menu) menu.style.display = 'none';
});

window.editMessage = function() {
  if (!activeMenuMessageId) return;
  const menu = document.getElementById('msgContextMenu');
  menu.style.display = 'none';

  // Get current message text
  const bubble = document.querySelector(`.msg-bubble[data-id="${activeMenuMessageId}"] .msg-text`);
  const currentText = bubble ? bubble.textContent.trim() : '';

  document.getElementById('editMessageInput').value = currentText;
  new bootstrap.Modal(document.getElementById('editMessageModal')).show();
};

window.saveEditMessage = function() {
  const newContent = document.getElementById('editMessageInput').value.trim();
  if (!newContent || !activeMenuMessageId) return;

  fetch('/messages/api/edit/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message_id: activeMenuMessageId,
      content: newContent
    })
  })
  .then(r => r.json())
  .then(data => {
    if (data.status === 'ok') {
      // Update the message in DOM
      const bubble = document.querySelector(`.msg-bubble[data-id="${activeMenuMessageId}"] .msg-text`);
      if (bubble) bubble.textContent = newContent;

      // Add edited indicator
      const timeEl = document.querySelector(`.msg-bubble[data-id="${activeMenuMessageId}"] .msg-time`);
      if (timeEl && !timeEl.querySelector('.msg-edited')) {
        timeEl.insertAdjacentHTML('afterbegin', '<span class="msg-edited">edited</span>');
      }

      // Close modal
      bootstrap.Modal.getInstance(document.getElementById('editMessageModal')).hide();
    }
  });
};

window.deleteMessage = function() {
  if (!activeMenuMessageId) return;
  const menu = document.getElementById('msgContextMenu');
  menu.style.display = 'none';

  if (!confirm('Delete this message?')) return;

  fetch('/messages/api/delete/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ message_id: activeMenuMessageId })
  })
  .then(r => r.json())
  .then(data => {
    if (data.status === 'ok') {
      // Update the message in DOM to show deleted state
      const bubble = document.querySelector(`.msg-bubble[data-id="${activeMenuMessageId}"]`);
      if (bubble) {
        bubble.classList.add('deleted');
        const content = bubble.querySelector('.msg-content');
        if (content) {
          const timeHtml = content.querySelector('.msg-time')?.outerHTML || '';
          content.innerHTML = `<div class="msg-text deleted-text"><i class="fa fa-ban"></i> This message was deleted</div>${timeHtml}`;
        }
        // Remove the action trigger
        const trigger = bubble.querySelector('.msg-actions-trigger');
        if (trigger) trigger.remove();
      }
    }
  });
};

})(); // End IIFE
