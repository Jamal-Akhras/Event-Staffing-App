import "./EmptyState.css";

type ErrorCardProps = {
  message: string;
  title?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
};

export function ErrorCard({ message, title = "Unable to load", action }: ErrorCardProps) {
  return (
    <div className="card error-card universal-error-card" role="alert">
      <span className="error-card-mark" aria-hidden="true" />
      <div>
        <h3 className="error-card-title">{title}</h3>
        <p className="error-card-message">{message}</p>
      </div>
      {action && (
        <button className="btn secondary" type="button" onClick={action.onClick}>
          {action.label}
        </button>
      )}
    </div>
  );
}
