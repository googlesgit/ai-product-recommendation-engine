export default function Toast({ message, onDismiss }) {
  if (!message) return null;
  return (
    <div className="toast" role="status">
      <span>{message}</span>
      <button type="button" className="toast-close" onClick={onDismiss} aria-label="Dismiss">
        ×
      </button>
    </div>
  );
}
