// src/components/SidebarItem.tsx
import React from 'react';
import './SidebarItem.css';

interface SidebarItemProps {
  icon?: React.ReactNode;
  text: string;
  isCollapsed: boolean;
  isRecent?: boolean; // To differentiate recent chat items
  href?: string; // Add this new prop
}

const SidebarItem: React.FC<SidebarItemProps> = ({ icon, text, isCollapsed, isRecent, href = "#" }) => { // Default href to #
  return (
    <li className={`sidebar-item ${isCollapsed ? 'collapsed' : ''} ${isRecent ? 'recent-item' : ''}`}>
      <a href={href}> {/* Use the href prop here */}
        {icon && <span className="sidebar-icon">{icon}</span>}
        {!isCollapsed && <span className="sidebar-text">{text}</span>}
      </a>
    </li>
  );
};

export default SidebarItem;