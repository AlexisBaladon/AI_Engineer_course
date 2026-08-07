import "./AdvertisementFooter.css";

export default function AdvertisementFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className="footer">
      <div className="footer-content">

        <div className="footer-section">
          <h3>NauAI</h3>

          <p>
            El asistente oficial de Nau64, diseñado para brindar respuestas
            rápidas, precisas y respaldadas por inteligencia artificial.
          </p>
        </div>

        <div className="footer-section">
          <h4>Creado por Alexis Baladón</h4>

          <p>
            Ingeniero en Computación especializado en Inteligencia Artificial,
            Procesamiento de Lenguaje Natural y desarrollo de asistentes
            conversacionales.
          </p>
        </div>

        <div className="footer-section">
          <h4>Conectemos</h4>

          <a
            className="footer-link"
            href="https://www.instagram.com/alexis.baladon/"
            target="_blank"
            rel="noopener noreferrer"
          >
            <svg
              className="footer-icon"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M7 2C4.24 2 2 4.24 2 7v10c0 2.76 2.24 5 5 5h10c2.76 0 5-2.24 5-5V7c0-2.76-2.24-5-5-5zm0 2h10c1.65 0 3 1.35 3 3v10c0 1.65-1.35 3-3 3H7c-1.65 0-3-1.35-3-3V7c0-1.65 1.35-3 3-3zm10.5 1a1.5 1.5 0 100 3 1.5 1.5 0 000-3zM12 7a5 5 0 100 10 5 5 0 000-10zm0 2a3 3 0 110 6 3 3 0 010-6z"/>
            </svg>

            Instagram
          </a>

          <a
            className="footer-link"
            href="https://uy.linkedin.com/in/alexis-baladon/es"
            target="_blank"
            rel="noopener noreferrer"
          >
            <svg
              className="footer-icon"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M4.98 3.5A1.75 1.75 0 106.73 5.25 1.75 1.75 0 004.98 3.5zM3.5 8h3v12h-3zm5 0h2.88v1.64h.04c.4-.76 1.38-1.64 2.84-1.64 3.04 0 3.6 2 3.6 4.6V20h-3v-6.1c0-1.45-.03-3.32-2.02-3.32-2.03 0-2.34 1.58-2.34 3.22V20h-3z"/>
            </svg>

            LinkedIn
          </a>
        </div>

      </div>

      <div className="footer-bottom">
        © {year} NauAI • Creado por Alexis Baladón
      </div>
    </footer>
  );
}