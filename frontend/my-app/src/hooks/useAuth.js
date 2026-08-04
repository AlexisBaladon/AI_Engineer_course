import { useEffect, useState } from "react";

const BACKEND_HOST =
    import.meta.env.VITE_BACKEND_HOST || "http://localhost";

const BACKEND_PORT =
    import.meta.env.VITE_BACKEND_PORT || 1235;

export default function useAuth() {
    const [user, setUser] = useState(null);
    const [checkingAuth, setCheckingAuth] = useState(true);
    const [showLogin, setShowLogin] = useState(false);

    async function login(username, password) {
        return fetch(
            `${BACKEND_HOST}:${BACKEND_PORT}/login`,
            {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    username: username.trim(),
                    password,
                }),
            }
        );
    }

    async function logout() {
        await fetch(
            `${BACKEND_HOST}:${BACKEND_PORT}/logout`,
            {
                method: "POST",
                credentials: "include",
            }
        );

        setUser(null);
    }

    async function checkAuth() {
        try {
            const response = await fetch(
                `${BACKEND_HOST}:${BACKEND_PORT}/auth/status`,
                {
                    credentials: "include",
                }
            );

            if (!response.ok) {
                setUser(null);
                return;
            }

            const data = await response.json();

            setUser({
                username: data.username,
            });
        } catch (err) {
            console.error(err);
            setUser(null);
        } finally {
            setCheckingAuth(false);
        }
    }

    async function handleLogin(username, password) {
        const response = await login(username, password);

        if (!response.ok) {
            return false;
        }

        await checkAuth();

        setShowLogin(false);

        return true;
    }

    function openLogin() {
        setShowLogin(true);
    }

    function closeLogin() {
        setShowLogin(false);
    }

    useEffect(() => {
        checkAuth();
    }, []);

    return {
        user,
        checkingAuth,
        showLogin,
        openLogin,
        closeLogin,
        login: handleLogin,
        logout,
        refresh: checkAuth,
    };
}