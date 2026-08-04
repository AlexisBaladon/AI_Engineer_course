import { useEffect, useState } from "react";

const BACKEND_HOST =
    import.meta.env.VITE_BACKEND_HOST || "http://localhost";

const BACKEND_PORT =
    import.meta.env.VITE_BACKEND_PORT || 1235;

const GUEST_CONVERSATIONS_KEY =
    "nau_guest_conversations";

export default function useConversations(user) {

    const [conversations, setConversations] = useState([]);

    const [currentConversationId,
        setCurrentConversationId] = useState(null);

    function createConversation() {

        const conversation = {
            id: crypto.randomUUID(),
            title: `Nueva conversación`,
            messages: [],
        };

        setConversations(prev => [
            ...prev,
            conversation,
        ]);

        setCurrentConversationId(
            conversation.id
        );

        return conversation;
    }

    function selectConversation(id) {
        setCurrentConversationId(id);
    }

    function updateConversation(
        conversationId,
        updater,
    ) {

        setConversations(prev =>
            prev.map(conversation =>
                conversation.id === conversationId
                    ? updater(conversation)
                    : conversation
            )
        );

    }

    function updateCurrentConversation(updater) {

        updateConversation(
            currentConversationId,
            updater,
        );

    }

    async function initialize() {

        // ---------- Guest ----------

        if (!user) {

            const saved =
                localStorage.getItem(
                    GUEST_CONVERSATIONS_KEY
                );

            if (saved) {

                try {

                    const loaded =
                        JSON.parse(saved);

                    if (loaded.length > 0) {

                        setConversations(
                            loaded
                        );

                        setCurrentConversationId(
                            loaded[0].id
                        );

                        return;
                    }

                } catch (err) {

                    console.error(err);

                }

            }

            createConversation();

            return;

        }

        // ---------- Logged ----------

        try {

            const response = await fetch(
                `${BACKEND_HOST}:${BACKEND_PORT}/conversations`,
                {
                    credentials: "include",
                }
            );

            if (!response.ok) {

                createConversation();

                return;

            }

            const data =
                await response.json();

            const loaded =
                Object.entries(data).map(
                    ([id, messages], index) => ({
                        id,
                        title:
                            `Conversación ${index + 1}`,
                        messages,
                    })
                );

            if (loaded.length === 0) {

                createConversation();

                return;

            }

            setConversations(loaded);

            setCurrentConversationId(
                loaded[0].id
            );

        }

        catch (err) {

            console.error(err);

            createConversation();

        }

    }

    useEffect(() => {

        initialize();

    }, [user]);

    useEffect(() => {

        if (user)
            return;

        localStorage.setItem(
            GUEST_CONVERSATIONS_KEY,
            JSON.stringify(conversations),
        );

    }, [conversations, user]);

    const currentConversation =
        conversations.find(
            c => c.id === currentConversationId
        ) ?? null;

    return {
        conversations,
        currentConversation,
        currentConversationId,
        createConversation,
        selectConversation,
        updateConversation,
        updateCurrentConversation,
        reload: initialize,
    };

}