import { useState } from "react";
import "./App.css";
import Sidebar from './components/common/Sidebar';
import ChatInterface from './components/common/ChatInterface'; // Import the new component

function App() {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [chatKey, setChatKey] = useState(Date.now()); // Add a key to force re-mount

  const toggleSidebar = () => {
    setIsSidebarCollapsed(prevState => !prevState);
  };

  const handleNewChat = () => {
    // By changing the key, we force the ChatInterface component to unmount and remount,
    // which naturally resets its internal state to its initial values.
    setChatKey(Date.now());
  };

  return (
    <div className={`app-container ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      <Sidebar
        isCollapsed={isSidebarCollapsed}
        toggleSidebar={toggleSidebar}
        onNewChat={handleNewChat}
      />

      <main className="main-content">
        {/* The key prop is essential here for resetting the chat */}
        <ChatInterface key={chatKey} />
      </main>
    </div>
  );
}

export default App;


