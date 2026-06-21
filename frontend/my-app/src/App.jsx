import { useRef, useState } from "react";
import Spinner from "./Spinner";

export default function App() {
  const inputRef = useRef(null);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  async function sendMessage() {
    const message = inputRef.current.value;
    if (!message) return;

    setLoading(true);
    setAnswer("");

    try {
      const res = await fetch(
        `http://localhost:1232/run_chain?query=${encodeURIComponent(message)}`
      );

      const data = await res.json();

      setAnswer(data.content);
    } catch (err) {
      setAnswer("Error connecting to backend.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ padding: 20, fontFamily: "sans-serif" }}>
      <h2>NauAI</h2>

      <input
        ref={inputRef}
        placeholder="Write a message..."
        style={{ width: 300, padding: 8 }}
      />

      <button onClick={sendMessage} style={{ marginLeft: 8 }}>
        Send
      </button>

      <div style={{ marginTop: 20 }}>
        <b>Answer:</b>

        {loading ? (
          <div style={{ marginTop: 10, display: "flex", alignItems: "center", gap: 10 }}>
            <Spinner />
            <span>Thinking...</span>
          </div>
        ) : (
          <p>{answer}</p>
        )}
      </div>
    </div>
  );
}