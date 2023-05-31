import React, { useState } from 'react';
import axios from 'axios';
import { useSpring, animated } from 'react-spring';
import './style.css';
import logo from './rattle_logo.svg';


function Chat() {
  const [prompt, setPrompt] = useState('');
  const [conversation, setConversation] = useState([]);
  const [isTyping, setIsTyping] = useState(false);

  const typingAnimation = useSpring({
    from: { width: '0%' },
    to: { width: '100%' },
    config: { duration: 1000 },
    reset: true,
  });

  const handleSubmit = async (event) => {
    event.preventDefault();
    setIsTyping(true);
    const response = await axios.post('http://localhost:8000/get_answer', { prompt });
    const generated = response.data.generated.replace(/\n/g, '<br />');
    const newMessage = { speaker: 'user', text: prompt };
    const botMessages = generated.split('. ').map((sentence) => ({ speaker: 'bot', text: sentence + '.' }));
    setConversation([...conversation, newMessage]);
    for (const message of botMessages) {
      setTimeout(() => {
        setConversation((conversation) => [...conversation, message]);
        if (conversation.length === 0) {
          setIsTyping(false);
        }
      }, 1000);
    }
    setPrompt('');
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <img src={logo} alt="Logo" className="logo" style={{ maxWidth: '20vw' }} />
        <h1 className="cool-header">Rattle Reliability Copilot</h1>
        <h2 className="cool-subheader">Streamline QA with our AI-powered chatbot - faster, smarter testing.</h2>
      </div>
      <div className="chat-messages">
        {conversation.map((message, index) => (
          <div className={`chat-message ${message.speaker}-message`} dangerouslySetInnerHTML={{ __html: message.text }}></div>
        ))}
        {isTyping && (
          <div className="chat-message bot-message">
            <animated.span className="typing-dots" style={typingAnimation}></animated.span>
          </div>
        )}
      </div>
      <form className="chat-input" onSubmit={handleSubmit}>
        <input type="text" value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="Example: Help me with some payment related test cases" required />
        <button type="submit">Submit</button>
      </form>
    </div>
  );
}

export default Chat;
