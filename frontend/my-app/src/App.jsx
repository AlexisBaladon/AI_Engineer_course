import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import { useRef, useState, useEffect } from "react";
import Spinner from "./Spinner";
import Login from "./Login";
import "./App.css";


export default function App() {
  const inputRef = useRef(null);
  
  const [showLogin, setShowLogin] = useState(false);  
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [user, setUser] = useState(null);
  const [checkingAuth, setCheckingAuth] = useState(true);

   useEffect(() => {
    async function checkAuth() {
      try {
        const response = await fetch(
          "http://localhost:1234/auth/status",
          {
            credentials: "include",
          }
        );

        if (!response.ok) {
          setUser(null);
          return;
        }

        const data = await response.json();

        setUser({
          username: data.username,
        });
      } catch (err) {
        console.error(err);
        setUser(null);
      } finally {
        setCheckingAuth(false);
      }
    }

    checkAuth();
  }, []);

  if (checkingAuth) {
    return <div>Loading...</div>;
  }

  async function handleLogout() {
    await fetch("http://localhost:1234/logout", {
        method: "POST",
        credentials: "include",
    });
    setUser(null);
  }

  async function sendPresetMessage(content) {
    inputRef.current.value = content;
    await sendMessage();
  }

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
          role: user ? "admin":"user", // TODO: Verify that user is logged using backend
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
          content: "Error conectándose al servidor. Por favor intente de nuevo o pruebe más tarde.",
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

        {
          showLogin && 
          <Login
            onCancel={() => setShowLogin(false)}
            onLogin={(user) => {
                setUser(user);
                setShowLogin(false);
            }}
        />}

         

        {/* MESSAGES */}
        <div className="messages">

          {messages.length === 0 && (
            <div className="empty-chat">

              <div className="empty-chat-content">

                <div className="assistant-avatar">
                  N
                </div>

                <h2 className="empty-chat-title">
                  ¡Hola! Soy NauAI 👋
                </h2>

                <p className="empty-chat-subtitle">
                  Puedo ayudarte a encontrar información sobre cursos,
                  torneos, formas de contacto y cualquier contenido de Nau64.
                </p>

                <div className="suggestion-grid">

                  <button
                    className="suggestion-card"
                    onClick={() =>
                      sendPresetMessage(
                        "¿Qué cursos hay disponibles en la academia?"
                      )
                    }
                  >
                    📚 Ver cursos disponibles
                  </button>

                  <button
                    className="suggestion-card"
                    onClick={() =>
                      sendPresetMessage(
                        "¿Cuáles han sido los últimos torneos realizados en Nau64? ¿Podrías mostrármelos en una tabla?"
                      )
                    }
                  >
                    🏆 Ver torneos realizados
                  </button>

                  <button
                    className="suggestion-card"
                    onClick={() =>
                      sendPresetMessage(
                        "En qué horarios se realizan clases en la academia? ¿En qué horario puedo pasar a visitar?"
                      )
                    }
                  >
                    🕜 Ver horarios
                  </button>

                  <button
                    className="suggestion-card"
                    onClick={() =>
                      sendPresetMessage(
                        "¿Cómo puedo contactarme con la academia? ¿Dónde están ubicados?"
                      )
                    }
                  >
                    📱 Obtener formas de contacto
                  </button>

                </div>

              </div>

            </div>
          )}

          {messages.map((m, i) => (
            <div
              key={i}
              className={`message ${m.role}`}
            >
              <div className="bubble">
                {
                  m.role === "user"
                    ? m.content
                    : (
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {m.content}
                      </ReactMarkdown>
                    )
                }
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
          <div className="top-bar">

            {!user ? (
              <button
                className="login-button"
                onClick={() => setShowLogin(true)}
              >
                Iniciar sesión
              </button>
            ) : (
              <div className="user-menu">

                <div className="user-chip">
                  <div className="avatar">
                    {user.username[0].toUpperCase()}
                  </div>

                  <span className="username">
                    {user.username}
                  </span>

                  <button
                    className="logout-button"
                    onClick={handleLogout}
                  >
                    Cerrar sesión
                  </button>
                </div>

              </div>
            )}

        </div>

    </div>
  );
}