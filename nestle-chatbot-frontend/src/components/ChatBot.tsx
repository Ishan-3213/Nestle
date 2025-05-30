import { useState, useEffect, useRef } from "react";
import "./ChatBot.css";

const Chatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<{ sender: string; text: string }[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isFirstApiCall, setIsFirstApiCall] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // When chat opens, add welcome message once
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([
        {
          sender: "bot",
          text: "Ready to serve you! I'm NestléBot to help you with anything.",
        },
      ]);
    }
  }, [isOpen]);

  // Scroll to bottom when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // For first API call, show waiting message while request is processing
      if (isFirstApiCall) {
        setMessages((prev) => [
          ...prev,
          { 
            sender: "bot", 
            text: "Please wait while we wake up the server. This may take 1-3 minutes for the first request..." 
          }
        ]);
        
        // Set timeout to show the user we're still working if it takes too long
        setTimeout(() => {
          setMessages((prev) => [
            ...prev,
            { 
              sender: "bot", 
              text: "Still working on your request... Server is initializing. Thanks for your patience!" 
            }
          ]);
        }, 60000); // Show after 1 minute
      }

      // Make the actual API call
      const response = await fetch(`https://nestle-th3j.onrender.com/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });
      
      const data = await response.json();

      // Remove any waiting messages if they exist
      setMessages(prev => prev.filter(msg => 
        !msg.text.includes("Please wait") && !msg.text.includes("Still working")
      ));
      
      // Add the actual response
      setMessages((prev) => [...prev, { sender: "bot", text: data.response }]);
      setIsFirstApiCall(false);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Error contacting server. Please try again." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chatbot-container">
      <button className="chatbot-toggle" onClick={() => setIsOpen(!isOpen)}>💬</button>

      {isOpen && (
        <div className="chatbot-window">
          <div className="chatbot-header">
            <span>Nestlé Assistant</span>
            <button className="chatbot-close" onClick={() => setIsOpen(false)}>×</button>
          </div>

          <div className="chatbot-messages">
            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.sender}`}>
                <div className="message-icon">
                  {msg.sender === "bot" ? (
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                      <path d="M12 2C13.1 2 14 2.9 14 4C14 4.74 13.6 5.39 13 5.73V7H14C17.87 7 21 10.13 21 14H22C22.55 14 23 14.45 23 15V18C23 18.55 22.55 19 22 19H21V20C21 21.1 20.1 22 19 22H5C3.9 22 3 21.1 3 20V19H2C1.45 19 1 18.55 1 18V15C1 14.45 1.45 14 2 14H3C3 10.13 6.13 7 10 7H11V5.73C10.4 5.39 10 4.74 10 4C10 2.9 10.9 2 12 2ZM7.5 13C6.12 13 5 14.12 5 15.5C5 16.88 6.12 18 7.5 18C8.88 18 10 16.88 10 15.5C10 14.12 8.88 13 7.5 13ZM16.5 13C15.12 13 14 14.12 14 15.5C14 16.88 15.12 18 16.5 18C17.88 18 19 16.88 19 15.5C19 14.12 17.88 13 16.5 13Z" />
                    </svg>
                  ) : (
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                      <path d="M12 4C13.1 4 14 4.9 14 6C14 7.1 13.1 8 12 8C10.9 8 10 7.1 10 6C10 4.9 10.9 4 12 4ZM12 14C16.42 14 20 15.79 20 18V20H4V18C4 15.79 7.58 14 12 14Z" />
                    </svg>
                  )}
                </div>
                <div className="message-text">{msg.text}</div>
              </div>
            ))}

            {isLoading && (
              <div className="message bot loading">
                <div className="message-icon">
                  <svg
                    viewBox="0 0 24 24"
                    width="20"
                    height="20"
                    fill="currentColor"
                    className="loading-icon"
                  >
                    <circle
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                      strokeDasharray="60"
                      strokeDashoffset="0"
                    >
                      <animate
                        attributeName="stroke-dashoffset"
                        values="0;240"
                        dur="1.5s"
                        repeatCount="indefinite"
                      />
                    </circle>
                  </svg>
                </div>
                <div className="message-text">
                  Processing<span className="dots">...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <div className="chatbot-input">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask something..."
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              disabled={isLoading}
            />
            <button onClick={sendMessage} disabled={isLoading}>
              ➤
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Chatbot;