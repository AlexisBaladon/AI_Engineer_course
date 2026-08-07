import "./Sidebar.css";
import { FaArrowLeft, FaArrowRight, FaComments, FaPlus } from "react-icons/fa";

export default function Sidebar({
    isOpen,
    onToggle,
    conversations,
    currentConversationId,
    onSelectConversation,
    onCreateConversation,
}) {
    return (
        <aside className={`sidebar ${isOpen ? "sidebar--open" : "sidebar--closed"}`}>

            <button
                className="sidebar-toggle"
                type="button"
                onClick={onToggle}
                aria-label={isOpen ? "Ocultar conversaciones" : "Mostrar conversaciones"}
                title={isOpen ? "Ocultar conversaciones" : "Mostrar conversaciones"}
            >
                {isOpen ? <FaArrowLeft aria-hidden="true" /> : <FaArrowRight aria-hidden="true" />}
            </button>

            <div className="sidebar-header">

                <button
                    className="new-chat-button"
                    onClick={onCreateConversation}
                >
                    <FaPlus aria-hidden="true" />
                    Nueva conversación
                </button>

            </div>

            <div className="conversation-list">

                {conversations.map((conversation, index) => {

                    const preview =
                        conversation.messages.find(
                            m => m.role === "user"
                        )?.content ?? "Nueva conversación";

                    return (
                        <button
                            key={conversation.id}
                            className={
                                `conversation-item ${
                                    conversation.id === currentConversationId
                                        ? "active"
                                        : ""
                                }`
                            }
                            onClick={() =>
                                onSelectConversation(
                                    conversation.id
                                )
                            }
                        >
                            <div className="conversation-title">
                                <FaComments aria-hidden="true" />
                                Conversación {index + 1}
                            </div>

                            <div className="conversation-preview">
                                {preview}
                            </div>

                        </button>
                    );
                })}

            </div>

        </aside>
    );
}
