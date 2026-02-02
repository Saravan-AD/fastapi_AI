import { useState } from "react";
import ReactMarkdown from "react-markdown";

export default function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [file, setFile] = useState(null);

  const sendMessage = async () => {
    if (!message.trim()) return;

    const newMessages = [...messages, { sender: "user", text: message }];
    setMessages(newMessages);

    const res = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: "saravan", message })
    });

    const data = await res.json();
    setMessages([...newMessages, { sender: "ai", text: data.reply }]);
    setMessage("");
  };

  const askDocument = async () => {
    if (!message.trim()) return;

    const newMessages = [...messages, { sender: "user", text: message }];
    setMessages(newMessages);

    const res = await fetch("http://localhost:8000/ask-doc", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: "saravan", message })
    });

    const data = await res.json();
    setMessages([...newMessages, { sender: "ai", text: data.reply }]);
    setMessage("");
  };

  const uploadFile = async () => {
    if (!file) return alert("Select a file first");

    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("http://localhost:8000/upload-doc", {
      method: "POST",
      body: formData
    });

    const data = await res.json();
    alert(data.message);
  };

  return (
    <div style={styles.container}>
      <h2>AI Knowledge Assistant</h2>

      <div style={styles.chatBox}>
        {messages.map((msg, index) => (
          <div
            key={index}
            style={{
              ...styles.message,
              alignSelf: msg.sender === "user" ? "flex-end" : "flex-start",
              backgroundColor: msg.sender === "user" ? "#1e4004" : "#1a1919"
            }}
          >
            <ReactMarkdown>{msg.text}</ReactMarkdown>
          </div>
        ))}
      </div>

      <div style={styles.inputArea}>
        <input
          style={styles.input}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type a message..."
        />
        <button onClick={sendMessage}>Chat</button>
        <button onClick={askDocument}>Ask Doc</button>
        <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      <button onClick={uploadFile}>Upload</button>
      </div>

      <hr />

      {/* <h3>Upload Document</h3> */}
      {/* <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      <button onClick={uploadFile}>Upload</button> */}
    </div>
  );
}

const styles = {
  container: {
    maxWidth: "100%",
    margin: "auto",
    fontFamily: "Arial"
  },
  chatBox: {
    height: "400px",
    border: "1px solid #ccc",
    padding: "10px",
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    gap: "10px",
    marginBottom: "10px"
  },
  message: {
    padding: "8px 12px",
    borderRadius: "12px",
    maxWidth: "75%"
  },
  inputArea: {
    display: "flex",
    gap: "5px"
  },
  input: {
    flex: 1,
    padding: "8px"
  }
};
