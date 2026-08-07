import "./AdvertisementFooter.css";
import {
  FaChessKnight,
  FaHeart,
  FaInstagram,
  FaLinkedinIn,
  FaMicrochip,
} from "react-icons/fa";

export default function AdvertisementFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className="footer">
      <div className="footer-content">

        <div className="footer-left">
          <div className="footer-brand">
            <FaChessKnight aria-hidden="true" />
            <h3>NauAI</h3>
          </div>

          <p>
            El asistente oficial de Nau64, diseñado para brindar respuestas
            rápidas, precisas y respaldadas por inteligencia artificial.
          </p>
        </div>

        <div className="footer-center">
          <div className="footer-title">
            <FaMicrochip aria-hidden="true" />
            <span>Desarrollado por</span>
          </div>

          <h4>Alexis Baladón</h4>

          <p>
            Ingeniero en Computación con experiencia en
            Procesamiento del Lenguaje Natural.
          </p>
        </div>

        <div className="footer-right">
          <div className="footer-title">
            <FaHeart aria-hidden="true" />
            <span>Conectemos</span>
          </div>

          <a
            className="footer-link"
            href="https://www.instagram.com/alexis.baladon/"
            target="_blank"
            rel="noopener noreferrer"
          >
            <FaInstagram className="footer-icon" aria-hidden="true" />

            Instagram
          </a>

          <a
            className="footer-link"
            href="https://uy.linkedin.com/in/alexis-baladon/es"
            target="_blank"
            rel="noopener noreferrer"
          >
            <FaLinkedinIn className="footer-icon" aria-hidden="true" />

            LinkedIn
          </a>
        </div>

      </div>

      <div className="footer-bottom">
        © {year} NauAI
      </div>
    </footer>
  );
}
