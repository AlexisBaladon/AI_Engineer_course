import { useRef, useState } from "react";

function App() {
  const inputRef = useRef(null);
  const [answer, setAnswer] = useState("");

  async function sendMessage() {
    const message = inputRef.current.value;

    if (!message) return;

    const res = await fetch(
      `http://localhost:1232/run_chain?query=${encodeURIComponent(message)}`
    );

    const data = await res.json();
    console.log(data)

    setAnswer(data.content);
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
        <p>{answer}</p>
      </div>
    </div>
  );
}

export default App;