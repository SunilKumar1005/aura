import React, { useEffect, useState, useRef } from 'react';
import './ChatMessages.css';

interface ChatMessageProps {
  type: 'user' | 'bot';
  content: string;
  isLoading?: boolean;
  onLoadComplete?: () => void;
  isNew?: boolean;
}

const LoadingDots: React.FC = () => (
  <div className="loading-dots">
    <div className="loading-dot" />
    <div className="loading-dot" />
    <div className="loading-dot" />
  </div>
);

const ChatMessage: React.FC<ChatMessageProps> = ({
  type,
  content,
  isLoading = false,
  onLoadComplete,
  isNew = true
}) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const renderContent = () => {
    if (isLoading && isNew && type === 'bot') {
      return <LoadingDots />;
    }
    // Always show full content for bot and user
    return (
      <div
        dangerouslySetInnerHTML={{
          __html: content
        }}
      />
    );
  };

  return (
    <div
      className={`chatbot-msg ${type} ${isLoading && isNew && type === 'bot' ? 'loading' : ''} ${isVisible ? 'visible' : ''}`}
      style={{ opacity: isVisible ? 1 : 0 }}
      aria-label={`${type === 'user' ? 'You' : 'AI Assistant'}`}
    >
      {renderContent()}
    </div>
  );
};

export default ChatMessage; 