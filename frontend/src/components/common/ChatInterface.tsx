import { useState, useEffect, useRef } from "react";
import SuggestionBox from './SuggestionBox';
import TypingIndicator from './TypingIndicator';
import './ChatInterface.css';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm'; // GitHub Flavored Markdown

interface Message {
    text: string;
    isUser: boolean;
}

const ChatInterface = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState("");
    const [currentSuggestions, setCurrentSuggestions] = useState<string[]>([]);
    const [isBotTyping, setIsBotTyping] = useState(false);

    const messagesEndRef = useRef<HTMLDivElement>(null);

    const defaultSuggestions = [
        "What is the primary objective of the ISMS at",
        "What are the eight guiding principles of the ISMS",
        "What is the role of the Management Observation Program",
        "What is the purpose of the Issues Management Program",
        "What is the goal of the ERM framework"
    ];

    useEffect(() => {
        if (messages.length === 0) {
            setCurrentSuggestions(defaultSuggestions);
        } else {
            setCurrentSuggestions([]);
        }
    }, [messages]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isBotTyping]);

    const handleSuggestionClick = (suggestion: string) => {
        setInputValue(suggestion);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!inputValue.trim()) return;

        const userMessage = { text: inputValue, isUser: true };
        setMessages((prevMessages) => [...prevMessages, userMessage]);
        const currentInput = inputValue;
        setInputValue("");
        setCurrentSuggestions([]);
        setIsBotTyping(true);

        try {
            const res = await fetch("http://localhost:3000/api/chat", { 
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: currentInput }),
            });

            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }

            const reader = res.body?.getReader();
            if (!reader) {
                throw new Error("Failed to get response reader");
            }

            const decoder = new TextDecoder();
            let botMessage = "";
            
            setMessages((prev) => [...prev, { text: "", isUser: false }]);

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const json = JSON.parse(line.substring(6));
                            if (json.reply) {
                                botMessage += json.reply;
                                setMessages((prev) => {
                                    const newMessages = [...prev];
                                    if (newMessages.length > 0 && !newMessages[newMessages.length - 1].isUser) {
                                        newMessages[newMessages.length - 1].text = botMessage;
                                    } else {
                                        newMessages.push({ text: botMessage, isUser: false });
                                    }
                                    return newMessages;
                                });
                            }
                        } catch (e) {
                            console.warn("Failed to parse SSE chunk:", line, e);
                        }
                    }
                }
            }
        } catch (err) {
            console.error("API Error:", err);
            setMessages((prev) => [...prev, { text: "Error: Could not get a reply. Please try again.", isUser: false }]);
        } finally {
            setIsBotTyping(false);
        }
    };

    return (
        <div className="chat-interface">
            <div className="chat-title">ESHQAI</div>

            <SuggestionBox
                suggestions={currentSuggestions}
                onSuggestionClick={handleSuggestionClick}
            />

            <div className="messages">
                {messages.map((msg, i) => (
                    <div key={i} className={`message ${msg.isUser ? "user" : "bot"}`}>
                        {msg.isUser ? (
                            msg.text
                        ) : (
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {msg.text}
                            </ReactMarkdown>
                        )}
                    </div>
                ))}
                {isBotTyping && (
                    <div className="message bot">
                        <TypingIndicator />
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <form className="chat-form" onSubmit={handleSubmit}>
                <textarea
                    className="chat-input"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="Type your message..."
                    rows={2}
                    onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                            e.preventDefault();
                            handleSubmit(e as any);
                        }
                    }}
                />
                <button type="submit" className="chat-send" disabled={isBotTyping}>Send</button>
            </form>
        </div>
    );
};

export default ChatInterface;
