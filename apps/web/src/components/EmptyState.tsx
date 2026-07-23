import "./EmptyState.css";

type EmptyStateProps = {
  title: string;
  message: string;
  action?: {
    label: string;
    onClick: () => void;
  };
};

export function EmptyState({ title, message, action }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <span className="empty-state-mark" aria-hidden="true" />
      <h3>{title}</h3>
      <p>{message}</p>
      {action && (
        <button className="btn secondary" onClick={action.onClick}>
          {action.label}
        </button>
      )}
    </div>
  );
}
