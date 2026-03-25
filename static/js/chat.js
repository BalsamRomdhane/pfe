/*
  chat.js provides a simple chat UI to send messages to the compliance chat endpoint.
*/

const chatEndpoint = '/api/compliance/chat/';

function initChat() {
  const chatWindow = document.getElementById('chatWindow');
  const chatForm = document.getElementById('chatForm');
  const chatInput = document.getElementById('chatInput');

  const typingIndicator = document.getElementById('chatTyping');

  const setTyping = (visible) => {
    if (!typingIndicator) return;
    typingIndicator.style.display = visible ? 'flex' : 'none';
  };

  const addMessage = (text, type = 'ai') => {
    if (!chatWindow) return;

    const message = document.createElement('div');
    message.className = `chat-message chat-message--${type}`;

    const avatar = document.createElement('div');
    avatar.className = 'chat-avatar';
    avatar.textContent = type === 'user' ? 'You' : 'AI';

    const bubble = document.createElement('div');
    bubble.className = `bubble ${type}`;
    bubble.textContent = text;

    if (type === 'user') {
      message.appendChild(bubble);
      message.appendChild(avatar);
    } else {
      message.appendChild(avatar);
      message.appendChild(bubble);
    }

    chatWindow.appendChild(message);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  };

  const sendMessage = async (message) => {
    addMessage(message, 'user');
    setTyping(true);

    const headers = typeof addCsrfHeader === 'function'
      ? addCsrfHeader({ 'Content-Type': 'application/json' })
      : { 'Content-Type': 'application/json' };

    const response = await fetch(chatEndpoint, {
      method: 'POST',
      headers,
      body: JSON.stringify({ message }),
      credentials: 'same-origin',
    });

    if (!response.ok) {
      addMessage('Failed to send message. Please try again.', 'ai');
      setTyping(false);
      return;
    }

    try {
      const data = await response.json();
      const reply = data.reply || data.message || 'No response received.';
      addMessage(reply, 'ai');
    } catch (err) {
      addMessage('Unable to parse response.', 'ai');
    } finally {
      setTyping(false);
    }
  };

  if (chatForm) {
    chatForm.addEventListener('submit', (event) => {
      event.preventDefault();
      const value = chatInput.value.trim();
      if (!value) return;
      chatInput.value = '';
      sendMessage(value);
    });
  }
}

window.initChat = initChat;
