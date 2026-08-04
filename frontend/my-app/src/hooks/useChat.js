import { useState } from "react";

const BACKEND_HOST =
    import.meta.env.VITE_BACKEND_HOST || "http://localhost";

const BACKEND_PORT =
    import.meta.env.VITE_BACKEND_PORT || 1235;

// TODO: confirm this matches your actual Flask/FastAPI route
const CHAT_ENDPOINT = `${BACKEND_HOST}:${BACKEND_PORT}/chat`;

const STORAGE_KEY = "nau_user_id";

function getUserId() {
  let userId = localStorage.getItem(STORAGE_KEY);

  if (!userId) {
    userId = crypto.randomUUID();
    localStorage.setItem(STORAGE_KEY, userId);
  }

  return userId;
}


export default function useChat({ 
    currentConversation, 
    updateCurrentConversation,
    currentConversationId,
}) {
    const [loading, setLoading] = useState(false);
    const [streaming, setStreaming] = useState(false);
    const userId = getUserId()

    async function sendMessage(content) {
        const updatedMessages = [
            ...currentConversation.messages,
            { role: "user", content },
        ];

        // Optimistically show the user's message immediately.
        updateCurrentConversation((conversation) => ({
            ...conversation,
            messages: updatedMessages,
        }));

        setLoading(true);

        try {
            const response = await fetch(CHAT_ENDPOINT, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                credentials: "include",
                // TODO: confirm this matches what your route expects
                // (e.g. maybe it wants { conversation_id, message } instead)
                body: JSON.stringify({
                    messages: updatedMessages,
                    stream: true,
                    user_id: userId,
                    conversation_id: currentConversationId,
                }),
            });

            if (!response.ok || !response.body) {
                throw new Error(
                    `Chat request failed with status ${response.status}`
                );
            }

            setLoading(false);
            setStreaming(true);

            // Add an empty assistant message that we'll fill in token by token.
            updateCurrentConversation((conversation) => ({
                ...conversation,
                messages: [
                    ...conversation.messages,
                    { role: "assistant", content: "" },
                ],
            }));

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });

                // SSE events are separated by a blank line ("\n\n").
                const events = buffer.split("\n\n");
                // Keep the last (possibly incomplete) chunk in the buffer.
                buffer = events.pop();

                for (const rawEvent of events) {
                    const line = rawEvent.trim();
                    if (!line.startsWith("data:")) continue;

                    const dataStr = line.slice("data:".length).trim();

                    if (dataStr === "[DONE]") {
                        continue;
                    }

                    let parsed;
                    try {
                        parsed = JSON.parse(dataStr);
                    } catch (e) {
                        console.error("Failed to parse SSE payload:", dataStr, e);
                        continue;
                    }

                    if (parsed.error) {
                        console.error("Stream error from backend:", parsed.error);
                        updateCurrentConversation((conversation) => {
                            const messages = [...conversation.messages];
                            const last = messages[messages.length - 1];
                            messages[messages.length - 1] = {
                                ...last,
                                content:
                                    last.content +
                                    `\n\n_Error: ${parsed.error}_`,
                            };
                            return { ...conversation, messages };
                        });
                        continue;
                    }

                    if (parsed.token) {
                        updateCurrentConversation((conversation) => {
                            const messages = [...conversation.messages];
                            const last = messages[messages.length - 1];
                            messages[messages.length - 1] = {
                                ...last,
                                content: last.content + parsed.token,
                            };
                            return { ...conversation, messages };
                        });
                    }
                }
            }
        } catch (err) {
            console.error("sendMessage failed:", err);
        } finally {
            setLoading(false);
            setStreaming(false);
        }
    }

    async function sendPresetMessage(content) {
        await sendMessage(content);
    }

    return {
        loading,
        streaming,
        sendMessage,
        sendPresetMessage,
    };
}