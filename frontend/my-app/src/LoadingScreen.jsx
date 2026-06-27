import Spinner from "./Spinner";
import "./LoadingScreen.css";

export default function LoadingScreen() {
  return (
    <div className="loading-screen">

      <div className="loading-card">

        <div className="loading-logo">
          NauAI
        </div>

        <Spinner />

        <p className="loading-text">
          Cargando...
        </p>

      </div>

    </div>
  );
}