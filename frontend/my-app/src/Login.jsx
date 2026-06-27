import { useState } from "react";
import "./Login.css"


export default function Login({ onLogin, onCancel }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();

    setError("");

    if (!username.trim()) {
      setError("Por favor ingresa un nombre de usuario.");
      return;
    }

    if (!password.trim()) {
      setError("Por favor ingresa una contraseña.");
      return;
    }

    try {
      const response = await fetch("http://localhost:1234/login", {
        method: "POST",
        credentials: "include", // Important: stores the auth cookie
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: username.trim(),
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError("Error al iniciar sesión.");
        return;
      }

      onLogin({
        username: username.trim(),
      });

    } catch (err) {
      console.error(err);
      setError("No fue posible conectarse al servidor.");
    }
  }

  return (
    <div className="login-overlay" onClick={onCancel}>

      <div
        className="login-card"
        onClick={(e) => e.stopPropagation()}
      >

        {/* Header */}
        <div className="login-header">
          <h2>Iniciar sesión</h2>

          <button
            className="close-button"
            onClick={onCancel}
          >
            ✕
          </button>
        </div>

        <p className="login-subtitle">
          Accede a características exclusivas de NauAI.
        </p>

        {/* Form */}
        <form onSubmit={handleSubmit}>

          <label>Usuario</label>
          <input
            type="text"
            value={username}
            placeholder="Ingresa tu nombre de usuario"
            onChange={(e) => {
              setUsername(e.target.value);
              setError("");
            }}
          />

          <label>Contraseña</label>
          <input
            type="password"
            value={password}
            placeholder="Ingresa tu contraseña"
            onChange={(e) => {
              setPassword(e.target.value);
              setError("");
            }}
          />

          {error && (
            <div className="login-error">
              {error}
            </div>
          )}

          {/* Buttons */}
          <div className="login-buttons">

            <button
              type="button"
              className="secondary-button"
              onClick={onCancel}
            >
              Cancelar
            </button>

            <button
              type="submit"
              className="primary-button"
            >
              Iniciar sesión
            </button>

          </div>

        </form>

      </div>

    </div>
  );
}