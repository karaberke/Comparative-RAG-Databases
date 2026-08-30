// src/components/HelpPopup.tsx
import React from "react";
import "./HelpPopup.css"; // You'll create this CSS file next
import { Close as CloseIcon } from "@mui/icons-material";

interface HelpPopupProps {
  onClose: () => void;
}

const HelpPopup: React.FC<HelpPopupProps> = ({ onClose }) => {
  return (
    <div className="popup-overlay" onClick={onClose}>
      <div className="popup-content" onClick={(e) => e.stopPropagation()}>
        {" "}
        {/* Prevents closing when clicking inside the popup */}
        <button
          className="popup-close-button"
          onClick={onClose}
          aria-label="Close popup"
        >
          <CloseIcon />
        </button>
        <h2>Welcome to Your ESH&Q Assistant!</h2>
        <p>
          This intelligent assistant is designed to help you quickly find
          answers to your Environmental, Safety, Health, and Quality (ESH&Q)
          questions without having to search through countless documents
          manually. Think of it as having a knowledgeable colleague who has read
          and memorized all your company's ESH&Q materials and can instantly
          provide you with the information you need.
        </p>
        <p>
          Type your question and the assistant will
          search through it's database to find the most
          relevant information and present it to you in an easy-to-understand
          format. Whether you're looking for safety procedures, environmental
          guidelines, quality standards, or health protocols, the assistant can
          help you locate the right information quickly. If the assistant cannot
          find an answer to your specific question in the available documents,
          it will tell you "I don't know" rather than guessing,
          ensuring you receive accurate and reliable information. This
          tool is designed to save you time and help you stay compliant with
          ESH&Q requirements by making critical information easily accessible
          whenever you need it.</p>
        {/* For more detailed information here, like: */}
        {/* <h3>Key Features:</h3>
        <ul>
          <li>Feature 1: [Short description]</li>
          <li>Feature 2: [Short description]</li>
          <li>Feature 3: [Short description]</li>
        </ul> */}
      </div>
    </div>
  );
};

export default HelpPopup;
