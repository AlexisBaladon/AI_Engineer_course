import "./spinner.css"

const spinnerStyle = {
  width: "18px",
  height: "18px",
  border: "3px solid #ccc",
  borderTop: "3px solid #333",
  borderRadius: "50%",
  animation: "spin 1s linear infinite"
};

export default function Spinner() {
  return (
    <div style={spinnerStyle} />
  );
}