import "./Sidebar.css";

export default function Sidebar({
    conversations,
    currentConversationId,
    onSelectConversation,
    onCreateConversation,
}) {
    return (
        <div className="sidebar">

            <div className="sidebar-header">

                <button
                    className="new-chat-button"
                    onClick={onCreateConversation}
                >
                    + Nueva conversación
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
                                Conversación {index+1}
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