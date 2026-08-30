import React from 'react';
import './TypingIndicator.css'; // We'll create this CSS next

const TypingIndicator: React.FC = () => {
  return (
    <div className="typing-indicator">
      <span></span>
      <span></span>
      <span></span>
    </div>
  );
};

export default TypingIndicator;