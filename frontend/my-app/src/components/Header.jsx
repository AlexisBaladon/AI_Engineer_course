import './Header.css'

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
                            Cerrar sesión
                        </button>

                    </div>

                </div>

            )}

        </div>
    );
}