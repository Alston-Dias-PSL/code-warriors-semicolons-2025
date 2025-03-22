import React, { useState } from 'react';
import logo from './logo.svg';
import backg from './background.png';
import './App.css';
import {
  MainContainer,
  ChatContainer,
  MessageList,
  Message,
  MessageInput,
  TypingIndicator
} from '@chatscope/chat-ui-kit-react';
import '@chatscope/chat-ui-kit-styles/dist/default/styles.min.css';
import { Paperclip, User, Bot } from 'lucide-react';

function App() {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [messages, setMessages] = useState([
    { message: "Hello! How can I help you today?", sender: "bot" }
  ]);
  const [isBotTyping, setIsBotTyping] = useState(false);

  const botResponses = [
    "Sure, I can help with that! Your travel request is noted.",
    "Absolutely! I'll get started on your travel plans.",
    "Travel request received. I'll handle it from here.",
    "Of course! Your request has been submitted.",
    "Happy to help! I'll take care of your travel arrangements."
  ];

  const handleSendMessage = (text) => {
    if (text.trim()) {
      const newMessage = { message: text, sender: "user" };
      setMessages((prev) => [...prev, newMessage]);
      setIsBotTyping(true);

      setTimeout(() => {
        const lowerText = text.toLowerCase();
        const response = lowerText.includes('travel') || lowerText.includes('trip')
          ? botResponses[Math.floor(Math.random() * botResponses.length)]
          : "Thank you for your message!";

        setMessages((prev) => [...prev, { message: response, sender: "bot" }]);
        setIsBotTyping(false);
      }, 1000);
    }
  };

  const handleFileUpload = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.onchange = async (e) => {
        const file = e.target.files[0];

        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch("http://127.0.0.1:8000/pre_travel", {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            console.log("Upload Response:", result);

            if (response.ok) {
                alert(`✅ File uploaded successfully: ${result.public_url}`);
            } else {
                alert(`❗ Error: ${result.detail}`);
            }
        } catch (error) {
            alert(`❗ Network error: ${error.message}`);
        }
    };
    input.click();
};


  return (
    <div className="App">
      {/* Floating Chat Button */}
      <button className="chat-button" onClick={() => setIsChatOpen(!isChatOpen)}>
        💬
      </button>

      {/* Chat Window */}
      {isChatOpen && (
        <div className="chat-window">
          <MainContainer>
            <ChatContainer>
              <MessageList typingIndicator={isBotTyping ? <TypingIndicator content="Typing..." /> : null}>
                {messages.map((msg, i) => (
                  <Message 
                    key={i} 
                    model={{
                      message: msg.message, 
                      sentTime: "just now", 
                      sender: msg.sender, 
                      direction: msg.sender === "user" ? "outgoing" : "incoming",
                      avatarSrc: msg.sender === 'user' ? <User size={24} /> : <Bot size={24} />
                    }} 
                  />
                ))}
              </MessageList>
              <MessageInput
                placeholder="Type your message..."
                onSend={handleSendMessage}
                attachButton={true}
                onAttachClick={handleFileUpload}
                attachButtonIcon={<Paperclip size={18} />}
              />
            </ChatContainer>
          </MainContainer>
          
        </div>
      )}

      {/* Styles */}
      <style>{`
        .chat-button {
          position: fixed;
          bottom: 20px;
          right: 20px;
          background-color: #007bff;
          color: white;
          border: none;
          border-radius: 50%;
          width: 56px;
          height: 56px;
          font-size: 24px;
          cursor: pointer;
          display: flex;
          justify-content: center;
          align-items: center;
          box-shadow: 0 8px 24px rgba(0,0,0,0.2);
          transition: background-color 0.3s, transform 0.2s;
        }

        .chat-button:hover {
          background-color: #0056b3;
          transform: scale(1.1);
        }

        .chat-window {
          position: fixed;
          bottom: 80px;
          right: 20px;
          width: 400px;
          height: 600px;
          background-color: #fff;
          box-shadow: 0 16px 40px rgba(0,0,0,0.15);
          border-radius: 16px;
          overflow: hidden;
          display: flex;
          flex-direction: column;
          animation: slideIn 0.3s ease-in-out;
        }

        @keyframes slideIn {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .cs-message--outgoing .cs-message__content {
          background-color: #007bff;
          color: white;
          border-radius: 18px;
          padding: 12px 16px;
          animation: fadeIn 0.4s;
        }

        .cs-message--incoming .cs-message__content {
          background-color: #FD7F39;
          color: white;
          border-radius: 18px;
          padding: 12px 16px;
          animation: fadeIn 0.4s;
        }

        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        .cs-message-list__scroll-wrapper {
          padding: 20px;
        }
      `}</style>
    </div>
  );
}

export default App;
