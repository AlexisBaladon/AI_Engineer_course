import ReactMarkdown from "react-markdown";

import { useRef, useState } from "react";
import Spinner from "./Spinner";

import "./App.css";


export default function App() {
  const inputRef = useRef(null);

  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);

  async function sendMessage() {
    const content = inputRef.current.value.trim();

    if (!content || loading || streaming) return;

    inputRef.current.value = "";

    const updatedMessages = [
      ...messages,
      { role: "user", content },
    ];

    setMessages(updatedMessages);
    setLoading(true);

    try {
      const res = await fetch("http://localhost:1232/run_chain", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: updatedMessages,
          stream: true,
        }),
      });

      if (!res.ok || !res.body) throw new Error();

      setLoading(false);
      setStreaming(true);

      let assistantContent = "";

      setMessages(prev => [
        ...prev,
        { role: "assistant", content: "" },
      ]);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data:")) continue;

          const payload = trimmed.slice(5).trim();
          if (payload === "[DONE]") continue;

          try {
            const { token } = JSON.parse(payload);

            assistantContent += token;

            setMessages(prev => {
              const copy = [...prev];
              copy[copy.length - 1] = {
                role: "assistant",
                content: assistantContent,
              };
              return copy;
            });
          } catch {}
        }
      }
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content: "Error connecting to backend.",
        },
      ]);
    } finally {
      setLoading(false);
      setStreaming(false);
    }
  }

  return (
    <div className="app">
      <div className="chat-container">

        {/* HEADER */}
        <div className="header">
          <div className="logo">NauAI</div>
          <div className="subtitle">El agente oficial de Nau64</div>
        </div>

        {/* MESSAGES */}
        <div className="messages">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`message ${m.role}`}
            >
              <div className="bubble">
                {m.role == "user" && m.content || <ReactMarkdown>{m.content}</ReactMarkdown>}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message assistant">
              <div className="bubble typing">
                <Spinner />
                <span>Pensando...</span>
              </div>
            </div>
          )}
        </div>

        {/* INPUT */}
        <div className="input-container">
          <input
            ref={inputRef}
            className="input"
            placeholder="Escriba a NauAI..."
            onKeyDown={e =>
              e.key === "Enter" && sendMessage()
            }
          />

          <button
            className="button"
            onClick={sendMessage}
            disabled={loading || streaming}
          >
            Enviar
          </button>
        </div>

      </div>
    </div>
  );
}