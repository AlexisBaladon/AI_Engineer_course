import "./Sidebar.css";

export default function Sidebar({
    conversations,
    currentConversationId,
    setCurrentConversationId,
    createConversation,
}) {
    return (
        <div className="sidebar">

            <div className="sidebar-header">

                <button
                    className="new-chat-button"
                    onClick={createConversation}
                >
                    + Nueva conversación
                </button>

            </div>

            <div className="conversation-list">

                {conversations.map((conversation) => {

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
                                setCurrentConversationId(
                                    conversation.id
                                )
                            }
                        >
                            <div className="conversation-title">
                                {conversation.title}
                            </div>

                            <div className="conversation-preview">
                                {preview}
                            </div>

                        </button>
                    );
                })}

            </div>

        </div>
    );
}