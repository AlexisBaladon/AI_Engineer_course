import { useRef, useState } from "react";
import Spinner from "./Spinner";

export default function App() {
  const inputRef = useRef(null);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);

  async function sendMessage() {
    const message = inputRef.current.value;
    if (!message) return;

    setLoading(true);
    setStreaming(false);
    setAnswer("");

    try {
      const res = await fetch(
        `http://localhost:1232/run_chain?query=${encodeURIComponent(message)}&stream=true`
      );

      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      if (!res.body) throw new Error("Streaming not supported by this browser.");

      setLoading(false);
      setStreaming(true);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop();

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || !trimmed.startsWith("data:")) continue;

          const payload = trimmed.slice("data:".length).trim();
          if (payload === "[DONE]") break;

          try {
            const { token } = JSON.parse(payload);
            if (token) setAnswer((prev) => prev + token);
          } catch {
            // Ignore malformed lines
          }
        }
      }
    } catch (err) {
      setAnswer("Error connecting to backend.");
    } finally {
      setLoading(false);
      setStreaming(false);
    }
  }

  return (
    <div style={{ padding: 20, fontFamily: "sans-serif" }}>
      <h2>NauAI</h2>

      <input
        ref={inputRef}
        placeholder="Write a message..."
        style={{ width: 300, padding: 8 }}
        onKeyDown={(e) => e.key === "Enter" && sendMessage()}
      />

      <button onClick={sendMessage} style={{ marginLeft: 8 }} disabled={loading || streaming}>
        Send
      </button>

      <div style={{ marginTop: 20 }}>
        <b>Answer:</b>

        {loading && (
          <div style={{ marginTop: 10, display: "flex", alignItems: "center", gap: 10 }}>
            <Spinner />
            <span>Thinking...</span>
          </div>
        )}

        {(streaming || answer) && (
          <p style={{ whiteSpace: "pre-wrap" }}>
            {answer}
            {streaming && <span style={{ opacity: 0.5 }}>▍</span>}
          </p>
        )}
      </div>
    </div>
  );
}