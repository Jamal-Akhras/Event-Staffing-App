type AppErrorFallbackProps = {
  resetError: () => void;
};

export function AppErrorFallback({ resetError }: AppErrorFallbackProps) {
  return (
    <div className="auth-page">
      <main className="auth-panel-right" style={{ width: "100%" }}>
        <div className="auth-form-wrap" role="alert">
          <h1 className="auth-heading">Something broke.</h1>
          <p className="auth-subheading">
            The page hit an unexpected error. Try again, and if it keeps happening, let us know.
          </p>
          <button type="button" className="auth-btn" onClick={resetError}>
            Reload
          </button>
        </div>
      </main>
    </div>
  );
}
