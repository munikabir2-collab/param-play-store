
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { signupUser } from "../api/client";

function Signup() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleSignup = async (event) => {
    event.preventDefault();

    setError("");
    setSuccess("");

    const cleanEmail = email.trim();

    if (!cleanEmail) {
      setError("Email required hai.");
      return;
    }

    if (password.length < 8) {
      setError(
        "Password kam se kam 8 characters ka hona chahiye."
      );
      return;
    }

    if (password !== confirmPassword) {
      setError(
        "Password aur confirm password match nahi kar rahe."
      );
      return;
    }

    try {
      setLoading(true);

      await signupUser({
        email: cleanEmail,
        password: password,
      });

      setSuccess(
        "Account successfully create ho gaya. Ab login karein."
      );

      setPassword("");
      setConfirmPassword("");

      setTimeout(() => {
        navigate("/login", {
          replace: true,
        });
      }, 1200);
    } catch (err) {
      console.error("Signup error:", err);

      const detail = err?.response?.data?.detail;

      if (Array.isArray(detail)) {
        setError(
          detail
            .map(
              (item) =>
                item?.msg || "Invalid signup data"
            )
            .join(", ")
        );
      } else {
        setError(
          detail ||
            err?.message ||
            "Signup failed. Please details check karein."
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
              DEVELOPER SIGNUP
            </p>

            <h1>
              Create your account
            </h1>

            <p className="auth-description">
              PARAM Play Store developer account
              banakar apne Android apps
              upload aur manage karein.
            </p>

            {error && (
              <div className="auth-error">
                <strong>
                  Signup Error
                </strong>

                <p>
                  {error}
                </p>
              </div>
            )}

            {success && (
              <div className="auth-success">
                <strong>
                  Account Created
                </strong>

                <p>
                  {success}
                </p>
              </div>
            )}

            <form
              className="auth-form"
              onSubmit={handleSignup}
            >

              <label htmlFor="signup-email">
                Email
              </label>

              <input
                id="signup-email"
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                placeholder="developer@example.com"
                autoComplete="email"
                required
                disabled={loading}
              />

              <label htmlFor="signup-password">
                Password
              </label>

              <input
                id="signup-password"
                type="password"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                placeholder="Minimum 8 characters"
                autoComplete="new-password"
                minLength={8}
                required
                disabled={loading}
              />

              <label htmlFor="signup-confirm-password">
                Confirm Password
              </label>

              <input
                id="signup-confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(event) =>
                  setConfirmPassword(event.target.value)
                }
                placeholder="Enter password again"
                autoComplete="new-password"
                minLength={8}
                required
                disabled={loading}
              />

              <button
                type="submit"
                className="auth-primary-button"
                disabled={loading}
              >
                {loading
                  ? "Creating account..."
                  : "Create Account"}
              </button>

            </form>

            <div className="auth-footer">

              <span>
                Already have an account?
              </span>

              <button
                type="button"
                className="auth-link-button"
                onClick={() => navigate("/login")}
              >
                Login
              </button>

            </div>

            <button
              type="button"
              className="auth-back-link"
              onClick={() => navigate("/")}
            >
              â† Back to marketplace
            </button>

          </div>

        </section>

      </main>

    </div>
  );
}

export default Signup;


