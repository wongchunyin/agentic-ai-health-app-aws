import { useState, useRef, useEffect } from 'react';
import Header from '../components/Header.jsx';
import '@material/web/button/filled-button.js';
import '@material/web/icon/icon.js';
import '@material/web/progress/circular-progress.js';

function ChatForm({ onSend }) {
  const [input, setInput] = useState('');

  const handleChange = (e) => {
    setInput(e.target.value);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim()) {
      onSend(input);
      setInput('');
    }
  };

  return (
    <form className="chat-input-area" autoComplete="off" onSubmit={handleSubmit}>
      <input
        type="text"
        className="chat-input"
        value={input}
        onChange={handleChange}
        placeholder="Type a message..."
        required
      />
      <md-filled-button type="submit" className="chat-send-btn">
        Send
        <md-icon slot="icon">send</md-icon>
      </md-filled-button>
    </form>
  );
}

function Chatbot() {
  const [chatLoaded, setChatLoaded] = useState(false);
  const [messages, setMessages] = useState([]);
  const [response, setResponse] = useState(null);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    const savedMessages = sessionStorage.getItem('chatMessages');
    if (savedMessages) {
      setMessages(JSON.parse(savedMessages));
    }
    setChatLoaded(true);

    const getSessionId = async () => {
      try {
        const response = await fetch('https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/get-chat-history', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + sessionStorage.getItem("id_token"),
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        if (result.conversations[0]) {
          sessionStorage.setItem('session_id', result.conversations[0].conversation_id);
        }

      } catch (e) {
        console.error(e.message);
      }
    }

    getSessionId();

  }, []);

  useEffect(() => {
    if (chatLoaded) {
      sessionStorage.setItem('chatMessages', JSON.stringify(messages));
    }
  }, [messages]);

  useEffect(() => {
    if (response) {
      setMessages((prev) => [
        ...prev,
        { text: response, sender: 'bot' }
      ]);
    }
  }, [response])

  const handleSend = async (text) => {
    const data = {
      chat_session_id: sessionStorage.getItem("session_id"),
      query: text,
    };

    setSending(true);
    setMessages((prev) => [
      ...prev,
      { text, sender: 'user' }
    ]);

    try {
      const response = await fetch('https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/ai-v2', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + sessionStorage.getItem("id_token"),
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (sessionStorage.getItem("session_id") === null) {
        sessionStorage.setItem('session_id', result.chat_session_id);
      }
      setResponse(result.response);
    
    } catch (e) {
      setError(e.message);
    }

    setSending(false);
  };

  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages]);

  return (
    <div>
      <Header />
      <div className="chat-main">
        <h2>AI Agent</h2>
        <div className="chat-container">
          <div className="chat-messages" id="chatMessages">
            {messages.map((msg, idx) => (
              <div key={idx} className={`chat-message ${msg.sender}`}>
                <div className="chat-bubble">{msg.text}</div>
              </div>
            ))}
            {sending && <md-circular-progress indeterminate></md-circular-progress>}
            <div ref={messagesEndRef} />
          </div>
          <ChatForm onSend={handleSend} />
        </div>
      </div>
    </div>
  );
}

export default Chatbot;
