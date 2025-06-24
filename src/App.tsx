  import React, { useState } from 'react';
// import logo from './logo.svg';
import './App.css';
import ChatBubble from './components/ChatBubble/ChatBubble';
import ChatBotUI from './components/ChatBotUI/ChatBotUI';

function App() {
  const [chatOpen, setChatOpen] = useState(false);

  return (
    <div className="App">
      <ChatBubble onClick={() => setChatOpen(true)} />
      <ChatBotUI open={chatOpen} onClose={() => setChatOpen(false)} />
    </div>
  );
}

export default App;
