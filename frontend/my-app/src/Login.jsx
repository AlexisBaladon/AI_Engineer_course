import { useState } from "react";
import "./Login.css"


export default function Login({ onLogin, onCancel, login }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");


  async function handleLoginSubmit(e) {
    e.preventDefault();

    setLoginError("");

    if (!username.trim()) {
      setLoginError("Por favor ingresa un nombre de usuario.");
      return;
    }

    if (!password.trim()) {
      setLoginError("Por favor ingresa una contraseña.");
      return;
    }

    try {
      const response = await login(username, password)

      if (!response.ok) {
        setLoginError("Error al iniciar sesión.");
        return;
      }

      onLogin({
        username: username.trim(),
      });

    } catch (err) {
      console.error(err);
      setLoginError("No fue posible conectarse al servidor.");
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
        <form onSubmit={handleLoginSubmit}>

          <label>Usuario</label>
          <input
            type="text"
            value={username}
            placeholder="Ingresa tu nombre de usuario"
            onChange={(e) => {
              setUsername(e.target.value);
              setLoginError("");
            }}
          />

          <label>Contraseña</label>
          <input
            type="password"
            value={password}
            placeholder="Ingresa tu contraseña"
            onChange={(e) => {
              setPassword(e.target.value);
              setLoginError("");
            }}
          />

          {loginError && (
            <div className="login-error">
              {loginError}
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