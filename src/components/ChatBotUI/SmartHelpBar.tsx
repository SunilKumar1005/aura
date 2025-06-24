import React, { useState, useEffect } from 'react';
import './SmartHelpBar.css';

interface HelpOption {
  id: string;
  label: string;
  action: () => void;
}

interface HelpCategory {
  id: string;
  icon: string;
  title: string;
  options: HelpOption[];
}

// Always keep the order for 2x2 grid
const HELP_CATEGORIES: HelpCategory[] = [
  {
    id: 'case',
    icon: '🔽',
    title: 'I need help with a case',
    options: [
      { id: 'case-status', label: 'Active Case', action: () => console.log('Case Status clicked') },
      { id: 'completed-cases', label: 'Completed Cases', action: () => console.log('Completed Cases clicked') }
    ]
  },
  {
    id: 'contact',
    icon: '📞',
    title: 'I want to talk to someone',
    options: [
      { id: 'callback', label: 'Request Callback', action: () => console.log('Callback requested') },
      { id: 'doctor', label: 'Radiologist', action: () => console.log('Doctor connect requested') }
    ]
  },
  {
    id: 'issues',
    icon: '🛠️',
    title: 'Facing an issue',
    options: [
      { id: 'technical', label: 'Technical Issue', action: () => console.log('Technical issue reported') },
      { id: 'finance', label: 'Finance Query', action: () => console.log('Finance query initiated') }
    ]
  },
  {
    id: 'other',
    icon: '📢',
    title: 'Other options',
    options: [
      { id: 'feedback', label: 'Feedback', action: () => console.log('Feedback requested') },
      { id: 'refer', label: 'Refer to 5C', action: () => console.log('Referral initiated') }
    ]
  }
];

interface SmartHelpBarProps {
  onOptionSelect: (option: { id: string; label: string }) => void;
  isUserTyping: boolean;
}

const ChevronTriple: React.FC<{ expanded: boolean }> = ({ expanded }) => (
  <svg
    width="20"
    height="20"
    viewBox="0 0 28 28"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={`chevron-triple ${expanded ? 'expanded' : ''}`}
  >
    <polyline points="5,10 14,19 23,10" stroke="#2176d2" strokeWidth="3.5" fill="none" strokeLinecap="round"/>
    <polyline points="7,6 14,13 21,6" stroke="#23235a" strokeWidth="2.5" fill="none" strokeLinecap="round"/>
    <polyline points="9,2 14,7 19,2" stroke="#23235a" strokeWidth="2" fill="none" strokeLinecap="round"/>
  </svg>
);

const SmartHelpBar: React.FC<SmartHelpBarProps> = ({ onOptionSelect, isUserTyping }) => {
  const [isExpanded, setIsExpanded] = useState(true); // Default expanded

  // Auto-collapse when user starts typing
  useEffect(() => {
    if (isUserTyping && isExpanded) {
      setIsExpanded(false);
    }
  }, [isUserTyping, isExpanded]);

  const handleOptionClick = (option: HelpOption) => {
    onOptionSelect(option);
    setIsExpanded(false);
  };

  // 2x2 grid split
  const firstRow = HELP_CATEGORIES.slice(0, 2);
  const secondRow = HELP_CATEGORIES.slice(2, 4);

  return (
    <div className={`smart-help-bar ${isExpanded ? 'expanded' : ''}`}>
      <div className="smart-help-content-2x2">
        <div className="smart-help-row">
          {firstRow.map(category => (
            <div key={category.id} className="help-category">
              <div className="category-header">
                <span className="category-icon">{category.icon}</span>
                <span className="category-title">{category.title}</span>
              </div>
              <div className="category-options">
                {category.options.map(option => (
                  <button
                    key={option.id}
                    className="help-option"
                    onClick={() => handleOptionClick(option)}
                    tabIndex={0}
                    type="button"
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div className="smart-help-row">
          {secondRow.map(category => (
            <div key={category.id} className="help-category">
              <div className="category-header">
                <span className="category-icon">{category.icon}</span>
                <span className="category-title">{category.title}</span>
              </div>
              <div className="category-options">
                {category.options.map(option => (
                  <button
                    key={option.id}
                    className="help-option"
                    onClick={() => handleOptionClick(option)}
                    tabIndex={0}
                    type="button"
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="smart-help-toggle-btn-bottom-wrapper" style={{ background: 'transparent' }}>
        <button
          className="smart-help-toggle-btn-bottom"
          aria-label={isExpanded ? 'Collapse help bar' : 'Expand help bar'}
          onClick={() => setIsExpanded((prev) => !prev)}
          tabIndex={0}
          type="button"
        >
          <ChevronTriple expanded={isExpanded} />
        </button>
      </div>
    </div>
  );
};

export default SmartHelpBar; 