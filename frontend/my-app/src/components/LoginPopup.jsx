import { useState } from "react";

import './LoginPopup.css'


export default function LoginPopup({
    visible,
    onLogin,
    onSuccess,
    onClose,
}) {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    if (!visible) {
        return null;
    }

    async function handleLogin() {
        if (!username.trim() || !password) {
            setError("Complete usuario y contraseña.");
            return;
        }

        setLoading(true);
        setError("");

        try {
            const response = await onLogin(
                username,
                password,
            );

            if (!response.ok) {
                setError(
                    "Usuario o contraseña incorrectos."
                );
                return;
            }

            onSuccess({
                username,
            });

            setUsername("");
            setPassword("");
        } catch (err) {
            console.error(err);

            setError(
                "No fue posible conectarse al servidor."
            );
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="login-overlay">

            <div className="login-card">

                <h2>
                    Iniciar sesión
                </h2>

                <label>Usuario</label>
                <input
                    placeholder="Usuario"
                    value={username}
                    onChange={(e) =>
                        setUsername(e.target.value)
                    }
                />

                <label>Contraseña</label>
                <input
                    type="password"
                    placeholder="Contraseña"
                    value={password}
                    onChange={(e) =>
                        setPassword(e.target.value)
                    }
                    onKeyDown={(e) =>
                        e.key === "Enter" &&
                        handleLogin()
                    }
                />

                {error && (
                    <div className="login-error">
                        {error}
                    </div>
                )}

                <div className="login-buttons">

                    <button
                        className="secondary-button"
                        onClick={onClose}
                        disabled={loading}
                    >
                        Cancelar
                    </button>

                    <button
                        className="primary-button"
                        onClick={handleLogin}
                        disabled={loading}
                    >
                        {loading
                            ? "Ingresando..."
                            : "Ingresar"}
                    </button>

                </div>

            </div>

        </div>
    );
}