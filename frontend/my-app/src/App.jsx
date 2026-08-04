import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import { useRef, useState, useEffect } from "react";
import Spinner from "./Spinner";
import Login from "./Login";
import LoadingScreen from "./LoadingScreen";
import Sidebar from "./Sidebar";
import "./App.css";


const BACKEND_HOST = import.meta.env.VITE_BACKEND_HOST || "http://localhost"
const BACKEND_PORT = import.meta.env.VITE_BACKEND_PORT || 1235


const STORAGE_KEY = "nau_user_id";
const GUEST_CONVERSATIONS_KEY = "nau_guest_conversations";


function getUserId() {
  let userId = localStorage.getItem(STORAGE_KEY);

  if (!userId) {
    userId = crypto.randomUUID();
    localStorage.setItem(STORAGE_KEY, userId);
  }

  return userId;
}


export default function App() {
  const inputRef = useRef(null);
  
  const [showLogin, setShowLogin] = useState(false);  
  const [conversations, setConversations] = useState(() => {
    const saved = localStorage.getItem(GUEST_CONVERSATIONS_KEY);

    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {}
    }

    return {
      id: crypto.randomUUID(),
      title: "Nueva conversación",
      messages: [],
    };
  });

  const [currentConversationId, setCurrentConversationId] = useState(0);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [user, setUser] = useState(null);
  const [checkingAuth, setCheckingAuth] = useState(true);

  function createConversation() {
    const conversation = {
      id: crypto.randomUUID(),
      title: `Nueva conversación`,
      messages: [],
    };

    setConversations(prev => [...prev, conversation]);
    setCurrentConversationId(conversation.id);
  }


  async function initializeConversations() {
    // Guest user
    if (!user) {
      const saved = localStorage.getItem(
        GUEST_CONVERSATIONS_KEY
      );

      if (saved) {
        try {
          const conversations = JSON.parse(saved);

          if (conversations.length > 0) {
            setConversations(conversations);
            setCurrentConversationId(conversations[0].id);
            return;
          }
        } catch (err) {
          console.error(err);
        }
      }

      createConversation();
      return;
  }

    try {
      const response = await fetch(
        `${BACKEND_HOST}:${BACKEND_PORT}/conversations`,
        {
          credentials: "include",
        }
      );

      if (!response.ok) {
        setConversations([])
        createConversation();
        return;
      }

      const data = await response.json();

      const loadedConversations = [];

      let conversation_numeric_index = 0;
      for (const [conversation_id, conversation] of Object.entries(data)) {
        conversation_numeric_index++;

        loadedConversations.push({
          id: conversation_id,
          title: `Conversación ${conversation_numeric_index}`,
          messages: conversation,
        });
      }

      if (loadedConversations.length === 0) {
        setConversations([])
        createConversation();
        return;
      }

      setConversations(loadedConversations);
      setCurrentConversationId(
        loadedConversations[0].id
      );
    } catch (err) {
      console.error(err);
      createConversation();
    }
  }


  async function login(username, password) {
      const response = await fetch(`${BACKEND_HOST}:${BACKEND_PORT}/login`, {
        method: "POST",
        credentials: "include", // Important: stores the auth cookie
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: username.trim(),
          password,
        }),
      });

      return response
  }


  async function checkAuth() {
      try {
        const response = await fetch(
          `${BACKEND_HOST}:${BACKEND_PORT}/auth/status`,
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

  async function handleLogout() {
    await fetch(`${BACKEND_HOST}:${BACKEND_PORT}/logout`, {
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
    const userId = getUserId()
    const content = inputRef.current.value.trim();

    if (!content || loading || streaming) return;

    inputRef.current.value = "";

    const updatedMessages = [
      ...messages,
      { role: "user", content },
    ];

    setConversations(prev =>
      prev.map(conv =>
        conv.id === currentConversationId
          ? {
              ...conv,
              messages: updatedMessages,
            }
          : conv
      )
    );
    setLoading(true);

    try {
      const res = await fetch(`${BACKEND_HOST}:${BACKEND_PORT}/chat`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: updatedMessages,
          stream: true,
          user_id: userId,
          conversation_id: currentConversationId,
        }),
      });

      if (!res.ok || !res.body) throw new Error();

      setLoading(false);
      setStreaming(true);

      let assistantContent = "";

      setConversations(prev =>
        prev.map(conv =>
          conv.id === currentConversationId
            ? {
                ...conv,
                messages: [
                  ...conv.messages,
                  {
                    role: "assistant",
                    content: "",
                  },
                ],
              }
            : conv
        )
      );

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

            setConversations(prev =>
              prev.map(conv => {
                if (conv.id !== currentConversationId)
                  return conv;

                const copy = [...conv.messages];

                copy[copy.length - 1] = {
                  role: "assistant",
                  content: assistantContent,
                };

                return {
                  ...conv,
                  messages: copy,
                };
              })
            );
          } catch {}
        }
      }
    } catch (err) {
      setConversations(prev =>
        prev.map(conv =>
          conv.id === currentConversationId
            ? {
                ...conv,
                messages: [
                  ...conv.messages,
                  {
                    role: "assistant",
                    content: "Error conectándose al servidor. Por favor intente de nuevo o pruebe más tarde.",
                  },
                ],
              }
            : conv
        )
      );
    } finally {
      setLoading(false);
      setStreaming(false);
    }
  }

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    if (checkingAuth) return;

    initializeConversations();
  }, [checkingAuth, user]);

  useEffect(() => {
    if (user) return;

    localStorage.setItem(
      GUEST_CONVERSATIONS_KEY,
      JSON.stringify(conversations)
    );
  }, [conversations, user]);

  
  
  const currentConversation =
    conversations.find(
      c => c.id === currentConversationId
    ) ?? conversations[0];

  const messages = currentConversation ? currentConversation.messages : [];

  if (checkingAuth) {
    return <LoadingScreen></LoadingScreen>;
  }

  return (
    <div className="app">
       <Sidebar
          conversations={conversations}
          currentConversationId={currentConversationId}
          setCurrentConversationId={setCurrentConversationId}
          createConversation={createConversation}
      />
      <div className="chat-container">

        {/* HEADER */}
        <div className="header">
          <div className="logo">NauAI</div>
          <div className="subtitle">El agente (aún no) oficial de Nau64</div>
        </div>

        {
          showLogin && 
          <Login
            onCancel={() => setShowLogin(false)}
            onLogin={(user) => {
                setUser(user);
                setShowLogin(false);
            }}
            login={login}
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
                        "¿Qué tipo de cursos hay disponibles en la academia?"
                      )
                    }
                  >
                    📚 Ver cursos disponibles
                  </button>

                  <button
                    className="suggestion-card"
                    onClick={() =>
                      sendPresetMessage(
                        "¿Cuáles han sido los últimos torneos realizados en Nau64?"
                      )
                    }
                  >
                    🏆 Ver últimos torneos
                  </button>

                  <button
                    className="suggestion-card"
                    onClick={() =>
                      sendPresetMessage(
                        "En qué horarios se realizan clases en la academia?"
                      )
                    }
                  >
                    🕜 Ver horarios
                  </button>

                  <button
                    className="suggestion-card"
                    onClick={() =>
                      sendPresetMessage(
                        "¿Podrías mostrarme los movimientos de alguna partida el sabatino del 6 junio de 2026?"
                      )
                    }
                  >
                    ♟️ Ver últimas jugadas
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