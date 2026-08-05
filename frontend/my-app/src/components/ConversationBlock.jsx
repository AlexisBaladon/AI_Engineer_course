import { useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import Spinner from "./Spinner";
import './ConversationBlock.css'

export default function ConversationBlock({
    messages,
    loading,
    streaming,
    onSendMessage,
    onSuggestion,
}) {
    const inputRef = useRef(null);

    async function handleSend() {
        const content = inputRef.current.value.trim();

        if (!content) return;

        inputRef.current.value = "";

        await onSendMessage(content);
    }

    async function sendSuggestion(message) {
        inputRef.current.value = message;
        await handleSend();
    }

    return (
        <div className="chat-container">

            {/* Header */}
            <div className="header">
                <div className="logo">
                    NauAI
                </div>

                <div className="subtitle">
                    El agente (aún no) oficial de Nau64
                </div>
            </div>

            {/* Messages */}

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
                                Puedo ayudarte a encontrar información sobre
                                cursos, torneos, formas de contacto y cualquier
                                contenido de Nau64.
                            </p>

                            <div className="suggestion-grid">

                                <button
                                    className="suggestion-card"
                                    onClick={() =>
                                        sendSuggestion(
                                            "¿Qué tipo de cursos hay disponibles en la academia?"
                                        )
                                    }
                                >
                                    📚 Ver cursos disponibles
                                </button>

                                <button
                                    className="suggestion-card"
                                    onClick={() =>
                                        sendSuggestion(
                                            "¿Cuáles han sido los últimos torneos realizados en Nau64?"
                                        )
                                    }
                                >
                                    🏆 Ver últimos torneos
                                </button>

                                <button
                                    className="suggestion-card"
                                    onClick={() =>
                                        sendSuggestion(
                                            "¿En qué horarios se realizan clases en la academia?"
                                        )
                                    }
                                >
                                    🕜 Ver horarios
                                </button>

                                <button
                                    className="suggestion-card"
                                    onClick={() =>
                                        sendSuggestion(
                                            "¿Cómo terminó la partida de la ronda 5 del sabatino del 6 de junio donde jugaron Leonel Recine y Evangelina Polito? ¿Podrías mostrarme algunos movimientos iniciales?"
                                        )
                                    }
                                >
                                    ♟️ Ver últimas jugadas
                                </button>

                            </div>

                        </div>

                    </div>

                )}

                {messages.map((message, index) => (

                    <div
                        key={index}
                        className={`message ${message.role}`}
                    >

                        <div className="bubble">

                            {message.role === "user" ? (

                                message.content

                            ) : (

                                <ReactMarkdown
                                    remarkPlugins={[remarkGfm]}
                                    components={{
                                        table: ({children}) => (
                                            <div className="table-wrapper">
                                                <table>{children}</table>
                                            </div>
                                        )
                                    }}
                                >
                                    {message.content}
                                </ReactMarkdown>

                            )}

                        </div>

                    </div>

                ))}

                {loading && (

                    <div className="message assistant">

                        <div className="bubble typing">

                            <Spinner />

                            <span>
                                Pensando...
                            </span>

                        </div>

                    </div>

                )}

            </div>

            {/* Input */}

            <div className="input-container">

                <input
                    ref={inputRef}
                    className="input"
                    placeholder="Escriba a NauAI..."
                    onKeyDown={(e) =>
                        e.key === "Enter" &&
                        handleSend()
                    }
                />

                <button
                    className="button"
                    onClick={handleSend}
                    disabled={loading || streaming}
                >
                    Enviar
                </button>

            </div>

        </div>
    );
}