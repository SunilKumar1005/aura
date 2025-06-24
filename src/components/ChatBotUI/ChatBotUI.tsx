import React, { useState, useEffect, useRef } from 'react';
import './ChatBotUI.css';
import botIcon from '../../assets/bot_icon.gif';
import SmartHelpBar from './SmartHelpBar';
import ChatMessage from './ChatMessage';

const HEADER_CYCLE_TEXTS = [
  'Instant help.',
  'Smarter workflows.',
  'Just Ask Aura.'
];

const GENIE_ANIMATION_DURATION = 700; // ms

const WELCOME_MESSAGE = `👋 Hi, I'm Aura, your AI assistant to help with any query!\nYou can select a specific issue from the options above ☝️\nor simply type your question below to get started.`;

interface Message {
  type: 'user' | 'bot';
  content: string;
  isLoading?: boolean;
  isNew?: boolean;
}

const ChatBotUI: React.FC<{
  open: boolean;
  onClose: () => void;
}> = ({ open, onClose }) => {
  const [headerIndex, setHeaderIndex] = useState(0);
  const [headerFade, setHeaderFade] = useState(true);
  const [genieState, setGenieState] = useState<'closed' | 'opening' | 'open' | 'closing'>('closed');
  const closeTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [inputValue, setInputValue] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [showWelcome, setShowWelcome] = useState(true);
  const endOfMessagesRef = useRef<HTMLDivElement>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Cycle header texts
  useEffect(() => {
    if (!open) return;
    const interval = setInterval(() => {
      setHeaderFade(false);
      setTimeout(() => {
        setHeaderIndex((prev) => (prev + 1) % HEADER_CYCLE_TEXTS.length);
        setHeaderFade(true);
      }, 350);
    }, 1800);
    return () => clearInterval(interval);
  }, [open]);

  // Prevent scroll on body when open
  useEffect(() => {
    if (open) document.body.style.overflow = 'hidden';
    else document.body.style.overflow = '';
    return () => { document.body.style.overflow = ''; };
  }, [open]);

  // Genie animation state logic
  useEffect(() => {
    if (open) {
      setGenieState('opening');
      const timer = setTimeout(() => setGenieState('open'), GENIE_ANIMATION_DURATION);
      return () => clearTimeout(timer);
    } else if (!open && genieState !== 'closed') {
      setGenieState('closing');
      closeTimeoutRef.current = setTimeout(() => setGenieState('closed'), GENIE_ANIMATION_DURATION);
      return () => {
        if (closeTimeoutRef.current) clearTimeout(closeTimeoutRef.current);
      };
    }
  }, [open]);

  // Custom close handler to play animation before calling parent's onClose
  const handleClose = () => {
    setGenieState('closing');
    closeTimeoutRef.current = setTimeout(() => {
      setGenieState('closed');
      onClose();
    }, GENIE_ANIMATION_DURATION);
  };

  // Map help bar option IDs to full sentences
  const HELP_OPTION_TO_SENTENCE: Record<string, string> = {
    'case-status': 'I need help with an active case',
    'completed-cases': 'I need help with completed cases',
    'callback': 'I want to request a callback',
    'doctor': 'I want to talk to a radiologist',
    'technical': 'I am facing a technical issue',
    'finance': 'I have a finance query',
    'feedback': 'I want to give feedback',
    'refer': 'I want to refer to 5C',
  };

  // Accept the full option object from SmartHelpBar
  const handleHelpOptionSelect = (option: { id: string, label: string }) => {
    const fullSentence = HELP_OPTION_TO_SENTENCE[option.id] || option.label || option.id;
    setShowWelcome(false);
    setInputValue(fullSentence);
    handleSend(fullSentence);
  };

  const handleSend = async (overrideInput?: string) => {
    const messageToSend = (overrideInput !== undefined ? overrideInput : inputValue).trim();
    if (!messageToSend || isStreaming) return;
    setShowWelcome(false);
    setIsStreaming(true);
    // Add user message
    setMessages(prev => [...prev, { 
      type: 'user', 
      content: messageToSend,
      isNew: true
    }]);
    // Add loading bot message (empty content)
    setMessages(prev => [...prev, { 
      type: 'bot', 
      content: '',
      isLoading: true,
      isNew: true
    }]);
    setInputValue('');
    if (inputRef.current) {
      inputRef.current.style.height = '36px'; // Reset textarea height
    }
    let streamError = false;
    try {
      const response = await fetch('http://localhost:8000/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: "demo_user",
          client_id: 3866,
          message: messageToSend
        })
      });
      if (!response.body) throw new Error('No response body');
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let fullText = '';
      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          fullText += chunk;
          setMessages(prev => {
            const newMessages = [...prev];
            const lastIdx = newMessages.length - 1;
            if (newMessages[lastIdx].type === 'bot') {
              newMessages[lastIdx] = {
                ...newMessages[lastIdx],
                content: fullText,
                isLoading: !done
              };
            }
            return newMessages;
          });
        }
      }
    } catch (error) {
      streamError = true;
      console.error('Error sending message:', error);
      setMessages(prev => {
        const newMessages = [...prev];
        const lastIdx = newMessages.length - 1;
        if (newMessages[lastIdx].type === 'bot') {
          newMessages[lastIdx] = {
            ...newMessages[lastIdx],
            content: 'Sorry, I encountered an error. Please try again.',
            isLoading: false
          };
        }
        return newMessages;
      });
    } finally {
      setIsStreaming(false);
      setMessages(prev => {
        const newMessages = [...prev];
        const lastIdx = newMessages.length - 1;
        if (newMessages[lastIdx].type === 'bot') {
          newMessages[lastIdx] = {
            ...newMessages[lastIdx],
            isLoading: false
          };
        }
        return newMessages;
      });
    }
  };

  useEffect(() => {
    if (endOfMessagesRef.current) {
      endOfMessagesRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Load chat history from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('chatbot_messages');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) setMessages(parsed);
      } catch {}
    }
  }, []);

  // Save chat history to localStorage on every update
  useEffect(() => {
    localStorage.setItem('chatbot_messages', JSON.stringify(messages));
  }, [messages]);

  // Always scroll to last message when chat UI is opened
  useEffect(() => {
    if (open && messages.length > 0) {
      setTimeout(() => {
        if (messagesContainerRef.current) {
          messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
        }
        if (endOfMessagesRef.current) {
          endOfMessagesRef.current.scrollIntoView({ behavior: 'auto' });
        }
      }, 120);
    }
  }, [open, messages.length]);

  // If closed, don't render the window at all
  let genieClass = 'genie-anim';
  if (genieState === 'opening') genieClass += ' genie-open';
  else if (genieState === 'open') genieClass += ' genie-open';
  else if (genieState === 'closing') genieClass += ' genie-close';
  if (genieState === 'closed') return null;

  return (
    <div 
      className={`chatbot-ui-backdrop${open ? ' open' : ''}`}
      onClick={handleClose}
      tabIndex={-1}
      style={{ 
        pointerEvents: open ? 'auto' : 'none',
        zIndex: open ? 4000 : -1 // Higher than bubble
      }}
    >
      <div
        className={`chatbot-ui-window ${genieClass}`}
        onClick={e => e.stopPropagation()}
        tabIndex={0}
        style={{
          pointerEvents: open ? 'auto' : 'none',
          zIndex: open ? 4001 : -1 // Higher than bubble
        }}
      >
        <div className="chatbot-ui-header">
          <img src={botIcon} alt="Bot" style={{ width: 36, height: 36, borderRadius: '50%', marginRight: 10, background: 'rgba(255,255,255,0.18)' }} />
          <span className="chatbot-ui-title">5C Aura AI Chatbot</span>
          <span className={`chatbot-ui-header-cycle${headerFade ? ' fade-in' : ' fade-out'}`}>{HEADER_CYCLE_TEXTS[headerIndex]}</span>
          <button className="chatbot-ui-close" onClick={handleClose} aria-label="Close">×</button>
        </div>
        
        <SmartHelpBar 
          onOptionSelect={handleHelpOptionSelect}
          isUserTyping={inputValue.length > 0}
        />

        <div className="chatbot-ui-messages" ref={messagesContainerRef}>
          {showWelcome && (
            <div className="chatbot-welcome-msg fade-float-in">
              <div className="welcome-ai-icon">
                <img src={botIcon} alt="AI Assistant" />
              </div>
              <div className="welcome-ai-text">
                <div className="welcome-title">👋 Hi, I'm Aura</div>
                <div className="welcome-desc">
                  Your AI assistant to help with any query.<br/>
                  <span className="welcome-highlight">Select an option above or type your question below to get started.</span>
                </div>
              </div>
            </div>
          )}
          {messages.map((msg, index) => (
            <ChatMessage
              key={index}
              type={msg.type}
              content={msg.content}
              isLoading={msg.isLoading}
              isNew={msg.isNew}
              onLoadComplete={() => {
                if (msg.type === 'bot' && msg.isLoading) {
                  setMessages(prev => {
                    const newMessages = [...prev];
                    newMessages[index] = { ...msg, isLoading: false };
                    return newMessages;
                  });
                }
              }}
            />
          ))}
          <div ref={endOfMessagesRef} />
        </div>

        <div className="chatbot-ui-input-row">
          <textarea
            className="chatbot-ui-input"
            placeholder="Type your message..."
            value={inputValue}
            ref={inputRef}
            onChange={e => {
              if (e.target.value.length <= 1000) setInputValue(e.target.value);
              if (inputRef.current) {
                inputRef.current.style.height = 'auto';
                inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 120) + 'px';
              }
            }}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            maxLength={3000}
            rows={1}
            style={{
              resize: 'none',
              minHeight: '36px',
              maxHeight: '120px',
              overflowY: 'auto',
              width: '100%',
              fontFamily: 'inherit',
              fontSize: '0.97rem',
              color: 'hsl(219, 36%, 36%)',
              background: isStreaming ? '#f3f3f3' : 'transparent',
              border: isStreaming ? '1.5px solid #d1d5db' : 'none',
              opacity: isStreaming ? 0.6 : 1,
              cursor: isStreaming ? 'not-allowed' : 'auto',
              outline: 'none',
              boxSizing: 'border-box',
            }}
            disabled={isStreaming}
          />
          <button 
            className="chatbot-ui-send"
            onClick={() => handleSend()}
            disabled={isStreaming}
            style={{
              opacity: isStreaming ? 0.5 : 1,
              cursor: isStreaming ? 'not-allowed' : 'pointer',
            }}
          >
            ➤
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatBotUI; 