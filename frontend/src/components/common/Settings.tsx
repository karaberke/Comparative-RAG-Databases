import React, { useState, useEffect } from "react"; 

import "./Settings.css"; 

import { Close as CloseIcon } from "@mui/icons-material"; 
  
// --- Constants for better maintainability --- 
const DATABASE_OPTIONS = [ 
  { id: "1", label: "Graph Database" }, 
  { id: "2", label: "Chroma Database" }, 
  { id: "3", label: "Quadrant Database" }, 
]; 

type LlmOption = "chatgpt" | "mistral"; 

const LLM_OPTIONS: { id: LlmOption; label: string }[] = [ 
  { id: "chatgpt", label: "GPT-OSS-120b" }, 
  { id: "mistral", label: "Mistral-Small" }, 
];

const API_ENDPOINT = "http://localhost:3000/api/user-settings"; 
  
// --- Type Definitions --- 
interface SettingsProps { 
  onClose: () => void; 
}   

interface UserSettings { 

  selectedDatabases: string[]; 

  selectedLlm: LlmOption; 

} 

// --- Component --- 
const Settings: React.FC<SettingsProps> = ({ onClose }) => { 

  const [selectedDatabases, setSelectedDatabases] = useState<string[]>([]); 

  const [selectedLlm, setSelectedLlm] = useState<LlmOption>("chatgpt"); // Default to 'chatgpt' 

  useEffect(() => { 

    const fetchUserSettings = async () => { 

      try { 

        const response = await fetch(API_ENDPOINT); 

        if (!response.ok) { 

          throw new Error(`HTTP error! status: ${response.status}`); 

        } 
        // Assuming the API returns an object with both settings 

        const data: UserSettings = await response.json(); 

        setSelectedDatabases(data.selectedDatabases || []); 

        setSelectedLlm(data.selectedLlm); 

      } catch (error) { 

        console.error("Error fetching user settings:", error); 

        // Silently fail or show a non-blocking error to the user 
      } 

    }; 

    fetchUserSettings(); 

  }, []); // Empty dependency array means this runs once on mount 


  const handleDatabaseToggle = (id: string) => { 

    setSelectedDatabases((prev) => 

      prev.includes(id) ? prev.filter((dbId) => dbId !== id) : [...prev, id] 

    ); 

  }; 

  const handleLlmChange = (event: React.ChangeEvent<HTMLInputElement>) => { 

    setSelectedLlm(event.target.value as LlmOption); 

  }; 

  const handleSave = async () => { 
    try { 

      const settingsToSave: UserSettings = { 
        selectedDatabases, 
        selectedLlm, 
      }; 

      const response = await fetch(API_ENDPOINT, { 
        method: "POST", 
        headers: { "Content-Type": "application/json" }, 
        body: JSON.stringify(settingsToSave), 

      }); 

      if (!response.ok) { 

        throw new Error("Failed to save settings to the server."); 

      } 
      // Optionally update localStorage as a fallback or for quick access 

      localStorage.setItem("userSettings", JSON.stringify(settingsToSave)); 
      alert("Settings saved successfully!"); 
      onClose(); 

    } catch (error) { 

      console.error("Error saving settings:", error); 

      alert("Failed to save settings. Please try again."); 
    } 
  }; 

  // Using a Set for O(1) lookups is more performant for `isChecked` 
  const selectedDbSet = new Set(selectedDatabases); 
  return ( 

    <div className="popup-overlay" onClick={onClose}> 
      <div className="popup-content" onClick={(e) => e.stopPropagation()}> 
        <button className="popup-close-button" onClick={onClose} aria-label="Close popup"> 
          <CloseIcon /> 
        </button> 
        <h2>Settings</h2> 
        <fieldset className="settings-group"> 
          <legend>Select Databases</legend> 
          {DATABASE_OPTIONS.map(({ id, label }) => ( 
            <label key={id}> 
              <input 
                type="checkbox" 
                checked={selectedDbSet.has(id)} 
                onChange={() => handleDatabaseToggle(id)} 
              /> 
              {label} 
            </label> 
          ))}
        </fieldset> 
        <br />
        <fieldset className="settings-group"> 
          <legend>Select Language Model (LLM)</legend> 
          {LLM_OPTIONS.map(({ id, label }) => ( 
            <label key={id}> 
              <input 
                type="radio" 
                name="llm" // `name` groups radio buttons 
                value={id} 
                checked={selectedLlm === id} 
                onChange={handleLlmChange} 
              /> 
              {label} 
            </label> 
          ))} 
        </fieldset> 
        <br />
        <button className="save-button" onClick={handleSave}> 
          Save Settings 
        </button> 
      </div> 
    </div> 
  ); 
}; 
export default Settings; 

 