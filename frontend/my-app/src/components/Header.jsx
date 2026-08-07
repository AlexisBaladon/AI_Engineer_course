import './Header.css'
import { FaRightFromBracket, FaRightToBracket } from "react-icons/fa6";

export default function Header({
    user,
    onLoginClick,
    onLogout,
}) {
    return (
        <div className="top-bar">

            {!user ? (

                <button
                    className="login-button"
                    onClick={onLoginClick}
                >
                    <FaRightToBracket aria-hidden="true" />
                    Iniciar sesión
                </button>

            ) : (

                <div className="user-menu">

                    <div className="user-chip">

                        <div className="avatar">
                            {user.username[0].toUpperCase()}
                        </div>

                        <span className="username">
                            {user.username}
                        </span>

                        <button
                            className="logout-button"
                            onClick={onLogout}
                        >
                            <FaRightFromBracket aria-hidden="true" />
                            Cerrar sesión
                        </button>

                    </div>

                </div>

            )}

        </div>
    );
}
