import { useRef, useState } from "react";
import Spinner from "./Spinner";

export default function App() {
  const inputRef = useRef(null);

  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);

  async function sendMessage() {
    const content = inputRef.current.value.trim();

    if (!content || loading || streaming) {
      return;
    }

    inputRef.current.value = "";

    const userMessage = {
      role: "user",
      content,
    };

    const updatedMessages = [
      ...messages,
      userMessage,
    ];

    setMessages(updatedMessages);

    setLoading(true);

    try {
      const res = await fetch(
        "http://localhost:1232/run_chain",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            messages: updatedMessages,
            stream: true,
          }),
        }
      );

      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`);
      }

      if (!res.body) {
        throw new Error("Streaming not supported.");
      }

      setLoading(false);
      setStreaming(true);

      let assistantContent = "";

      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content: "",
        },
      ]);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          break;
        }

        buffer += decoder.decode(value, {
          stream: true,
        });

        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();

          if (
            !trimmed ||
            !trimmed.startsWith("data:")
          ) {
            continue;
          }

          const payload = trimmed
            .slice("data:".length)
            .trim();

          if (payload === "[DONE]") {
            continue;
          }

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
          } catch {
            // Ignore malformed chunks
          }
        }
      }
    } catch (error) {
      console.error(error);

      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content:
            "Error connecting to backend.",
        },
      ]);
    } finally {
      setLoading(false);
      setStreaming(false);
    }
  }

  return (
    <div
      style={{
        padding: 20,
        fontFamily: "sans-serif",
      }}
    >
      <h2>NauAI</h2>

      <div
        style={{
          marginBottom: 20,
        }}
      >
        {messages.map((message, index) => (
          <div
            key={index}
            style={{
              marginBottom: 12,
            }}
          >
            <strong>
              {message.role === "user"
                ? "You"
                : "NauAI"}
              :
            </strong>

            <div
              style={{
                whiteSpace: "pre-wrap",
              }}
            >
              {message.content}
            </div>
          </div>
        ))}
      </div>

      {loading && (
        <div
          style={{
            display: "flex",
            gap: 10,
            alignItems: "center",
            marginBottom: 12,
          }}
        >
          <Spinner />
          <span>Thinking...</span>
        </div>
      )}

      <input
        ref={inputRef}
        placeholder="Write a message..."
        style={{
          width: 400,
          padding: 8,
        }}
        onKeyDown={e =>
          e.key === "Enter" &&
          sendMessage()
        }
      />

      <button
        onClick={sendMessage}
        disabled={loading || streaming}
        style={{
          marginLeft: 8,
        }}
      >
        Send
      </button>
    </div>
  );
}