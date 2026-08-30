// src/components/Sidebar.tsx
import { useState } from 'react';
import './Sidebar.css';
import SidebarItem from './SidebarItem';
import HelpPopup from './HelpPopup';
import Settings from './Settings'; 
import {
  Menu as MenuIcon,
  LightbulbOutlined as LightbulbIcon,
  ChatBubbleOutline as ChatIcon,
  HelpOutline as HelpIcon,
  SettingsOutlined as SettingsIcon,
  InfoOutlined as InfoIcon,
  Add as AddIcon,
} from '@mui/icons-material';

const supportLink="https://apps.gov.powerapps.us/play/e/c15ee2aa-54b4-e0d1-9641-3fac269fa813/a/723833f3-ed57-4f77-b002-96123a3c9b7f?tenantId=4cf464b7-869a-4236-8da2-a98566485554&hint=1ed8feb1-d2ee-4f5e-809e-d13573abfb58&sourcetime=1731623837848&source=portal";

interface SidebarProps {
  isCollapsed: boolean;
  toggleSidebar: () => void;
  onNewChat: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, toggleSidebar, onNewChat }) => {
  // State to control the visibility of the Help popup
  const [isHelpPopupOpen, setIsHelpPopupOpen] = useState(false);
  const [isSettingsPopupOpen, setisSettingsPopupOpen] = useState(false);

  const openHelpPopup = () => {
    setIsHelpPopupOpen(true);
  };

  const closeHelpPopup = () => {
    setIsHelpPopupOpen(false);
  };

  const openSettingsPopup = () => {
    setisSettingsPopupOpen(true);
  };

  const closSettingsPopup = () => {
    setisSettingsPopupOpen(false);
  };
  
  return (
    <div className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <button className="menu-button" onClick={toggleSidebar} aria-label="Toggle sidebar">
          <MenuIcon />
        </button>

        {!isCollapsed && (
          <div className="new-chat-button" role="button" tabIndex={0} onClick={onNewChat}>
            <AddIcon />
            <span>New Chat</span>
          </div>
        )}
      </div>

      <nav className="sidebar-nav">
        <ul>
          <SidebarItem icon={<LightbulbIcon />} text="Explore" isCollapsed={isCollapsed} />
          {!isCollapsed && (
            <>
              <SidebarItem icon={<ChatIcon />} text="Recent" isCollapsed={isCollapsed} />
              <div className="recent-items-list">
                {/* These will continue to be standard links */}
                <SidebarItem text="FAQs" isCollapsed={isCollapsed} isRecent />
                <SidebarItem text="Documents" isCollapsed={isCollapsed} isRecent />
              </div>
            </>
          )}
          {isCollapsed && (
            <SidebarItem icon={<ChatIcon />} text="Recent" isCollapsed={isCollapsed} />
          )}
        </ul>
      </nav>

      <div className="sidebar-footer">
        <ul>
          {/* Custom "Help" list item with an onClick handler */}
          <li
            className={`sidebar-item ${isCollapsed ? 'collapsed' : ''}`}
            onClick={openHelpPopup} // Directly attach the function here
            role="button" // Indicate it's interactive for accessibility
            tabIndex={0} // Make it focusable
            onKeyDown={(e) => { // Handle keyboard accessibility for Enter/Space
                if (e.key === 'Enter' || e.key === ' ') {
                    openHelpPopup();
                }
            }}
          >
            {/* The content structure matches SidebarItem for consistent styling */}
            <a href="#" className="sidebar-item-content-wrapper"> {/* Keep <a> if SidebarItem.css styles it */}
                <span className="sidebar-icon"><InfoIcon /></span>
                {!isCollapsed && <span className="sidebar-text">Help</span>}
            </a>
          </li>
          <li
            className={`sidebar-item ${isCollapsed ? 'collapsed' : ''}`}
            onClick={openSettingsPopup} // Directly attach the function here
            role="button" // Indicate it's interactive for accessibility
            tabIndex={0} // Make it focusable
            onKeyDown={(e) => { // Handle keyboard accessibility for Enter/Space
                if (e.key === 'Enter' || e.key === ' ') {
                    openSettingsPopup();
                }
            }}
          >
             {/* The content structure matches SidebarItem for consistent styling */}
            <a href="#" className="sidebar-item-content-wrapper"> {/* Keep <a> if SidebarItem.css styles it */}
                <span className="sidebar-icon"><SettingsIcon /></span>
                {!isCollapsed && <span className="sidebar-text">Settings</span>}
            </a>
          </li>
          {/* Other footer items can still use SidebarItem */}
          <SidebarItem icon={<HelpIcon />} text="Support" isCollapsed={isCollapsed} href={supportLink} />
          </ul>
      </div>

      {/* Conditionally render the HelpPopup */}
      {isHelpPopupOpen && <HelpPopup onClose={closeHelpPopup} />}
      {isSettingsPopupOpen && <Settings onClose={closSettingsPopup} />}
    </div>
  );
};

export default Sidebar;