
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginUser } from "../api/client";

function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (event) => {
    event.preventDefault();

    const cleanEmail = email.trim();

    if (!cleanEmail || !password) {
      setError("Email aur password required hai.");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const data = await loginUser(
        cleanEmail,
        password
      );

      if (!data?.access_token) {
        throw new Error(
          "Login response mein access token nahi mila."
        );
      }

      localStorage.setItem(
        "PARAM Play Store_token",
        data.access_token
      );

      navigate("/dashboard", {
        replace: true,
      });
    } catch (err) {
      console.error(
        "Login error:",
        err
      );

      const detail =
        err.response?.data?.detail;

      if (Array.isArray(detail)) {
        setError(
          detail
            .map(
              (item) =>
                item?.msg || "Invalid login data"
            )
            .join(", ")
        );
      } else {
        setError(
          detail ||
            err.message ||
            "Login failed. Email ya password check karein."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header className="topbar">
        <div>
          <div className="brand">
            PARAM Play Store
          </div>

          <div className="subtitle">
            Developer App Marketplace
          </div>
        </div>

        <button
          type="button"
          className="refresh-button"
          onClick={() => navigate("/")}
        >
          Browse Apps
        </button>
      </header>

      <main className="container">
        <section className="auth-page">
          <div className="auth-card">
            <p className="eyebrow">
              DEVELOPER LOGIN
            </p>

            <h1>
              Login to PARAM Play Store
            </h1>

            <p className="auth-description">
              Apne developer dashboard mein
              login karke apps upload aur
              manage karein.
            </p>

            {error && (
              <div className="auth-error">
                <strong>
                  Login Error
                </strong>

                <p>{error}</p>
              </div>
            )}

            <form
              className="auth-form"
              onSubmit={handleLogin}
            >
              <label htmlFor="email">
                Email
              </label>

              <input
                id="email"
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(
                    event.target.value
                  )
                }
                placeholder="developer@example.com"
                autoComplete="email"
                required
                disabled={loading}
              />

              <label htmlFor="password">
                Password
              </label>

              <input
                id="password"
                type="password"
                value={password}
                onChange={(event) =>
                  setPassword(
                    event.target.value
                  )
                }
                placeholder="Password"
                autoComplete="current-password"
                required
                disabled={loading}
              />

              <button
                type="submit"
                className="auth-primary-button"
                disabled={loading}
              >
                {loading
                  ? "Logging in..."
                  : "Login"}
              </button>
            </form>

            <div className="auth-footer">
              <span>
                New developer?
              </span>

              <button
                type="button"
                className="auth-link-button"
                onClick={() =>
                  navigate("/signup")
                }
              >
                Create an account
              </button>
            </div>

            <button
              type="button"
              className="auth-back-link"
              onClick={() =>
                navigate("/")
              }
            >
              â† Back to marketplace
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}

export default Login;


