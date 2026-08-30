import React from 'react';
import './SuggestionBox.css'; // Assuming you put the CSS in SuggestionBox.css or a global CSS file

interface SuggestionBoxProps {
  suggestions: string[];
  onSuggestionClick: (suggestion: string) => void;
}

const SuggestionBox: React.FC<SuggestionBoxProps> = ({ suggestions, onSuggestionClick }) => {
  if (suggestions.length === 0) {
    return null; // Don't render if there are no suggestions
  }

  return (
    <div className="suggestions-container">
      {suggestions.map((suggestion, index) => (
        <button
          key={index} // In a real app, use a unique ID for the suggestion if available
          className="suggestion-chip"
          onClick={() => onSuggestionClick(suggestion)}
        >
          {suggestion}
        </button>
      ))}
    </div>
  );
};

export default SuggestionBox;


