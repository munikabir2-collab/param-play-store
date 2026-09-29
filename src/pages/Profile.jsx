
import { useEffect, useState } from "react";

import {
  Link,
  useNavigate,
} from "react-router-dom";

import {
  getCurrentUser,
} from "../api/client";


function Profile() {
  const navigate = useNavigate();

  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const token =
      localStorage.getItem("PARAM Play Store_token");

    const loadProfile = async () => {
      if (!token) {
        setLoading(false);
        setUser(null);
        return;
      }

      try {
        setLoading(true);
        setError("");

        const data =
          await getCurrentUser(token);

        setUser(data);
      } catch (err) {
        console.error(
          "Profile load error:",
          err
        );

        if (
          err.response?.status === 401
        ) {
          localStorage.removeItem(
            "PARAM Play Store_token"
          );

          setUser(null);

          setError(
            "Your session has expired. Please login again."
          );

          return;
        }

        if (
          err.response?.status === 404
        ) {
          setUser(null);

          setError(
            "Profile API (/auth/me) backend me available nahi hai."
          );

          return;
        }

        setUser(null);

        setError(
          err.response?.data?.detail ||
            err.message ||
            "Profile load nahi ho paya."
        );
      } finally {
        setLoading(false);
      }
    };

    loadProfile();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem(
      "PARAM Play Store_token"
    );

    navigate("/");
  };

  const handleLogin = () => {
    navigate("/login");
  };

  const handleSignup = () => {
    navigate("/signup");
  };

  const handleDashboard = () => {
    navigate("/dashboard");
  };

  const getInitial = () => {
    if (user?.full_name) {
      return user.full_name
        .charAt(0)
        .toUpperCase();
    }

    if (user?.email) {
      return user.email
        .charAt(0)
        .toUpperCase();
    }

    return "U";
  };


  return (
    <div className="page">

      {/* =================================================
          TOP BAR
          ================================================= */}

      <header className="topbar">

        <div>

          <Link
            to="/"
            style={{
              textDecoration: "none",
              color: "inherit",
            }}
          >
            <div className="brand">
              PARAM Play Store
            </div>
          </Link>

          <div className="subtitle">
            Developer App Marketplace
          </div>

        </div>


        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            flexWrap: "wrap",
            justifyContent: "flex-end",
          }}
        >

          <Link
            to="/"
            className="refresh-button"
            style={{
              textDecoration: "none",
            }}
          >
            Marketplace
          </Link>


          {user && (
            <button
              type="button"
              className="refresh-button"
              onClick={handleLogout}
            >
              Logout
            </button>
          )}

        </div>

      </header>


      {/* =================================================
          MAIN
          ================================================= */}

      <main className="container">

        <section className="profile-page-card">

          {/* =================================================
              PROFILE HEADER
              ================================================= */}

          <div className="profile-header">

            <div>

              <p className="eyebrow">
                USER ACCOUNT
              </p>

              <h1>
                User Profile
              </h1>

              <p className="hero-text">
                अपने PARAM Play Store account और developer information को देखें।

              </p>

            </div>


            {user && (
              <div className="profile-avatar">
                {getInitial()}
              </div>
            )}

          </div>


          {/* =================================================
              LOADING
              ================================================= */}

          {loading && (

            <div className="state-card">

              <strong>
                Profile
              </strong>

              <p>
                Profile load ?? ??? ??...
              </p>

            </div>

          )}


          {/* =================================================
              ERROR
              ================================================= */}

          {!loading && error && (

            <div className="error-card">

              <strong>
                Profile Error
              </strong>

              <p>
                {error}
              </p>


              <div
                className="profile-actions"
              >

                <button
                  type="button"
                  className="primary-button"
                  onClick={handleLogin}
                >
                  Developer Login
                </button>


                <button
                  type="button"
                  className="secondary-button"
                  onClick={handleSignup}
                >
                  Create Account
                </button>


                <button
                  type="button"
                  className="refresh-button"
                  onClick={() =>
                    window.location.reload()
                  }
                >
                  Retry
                </button>

              </div>

            </div>

          )}


          {/* =================================================
              NOT LOGGED IN
              ================================================= */}

          {!loading &&
            !error &&
            !user && (

              <div className="profile-login-card">

                <div className="profile-login-icon">
                  U
                </div>

                <h2>
                  Login to your account
                </h2>

                <p>
                  Profile information देखने के लिए पहले login करें।

                </p>


                <div
                  className="profile-actions"
                >

                  <button
                    type="button"
                    className="primary-button"
                    onClick={handleLogin}
                  >
                    Developer Login
                  </button>


                  <button
                    type="button"
                    className="secondary-button"
                    onClick={handleSignup}
                  >
                    Create Account
                  </button>

                </div>

              </div>

            )}


          {/* =================================================
              USER PROFILE
              ================================================= */}

          {!loading &&
            !error &&
            user && (

              <div className="profile-content">


                {/* =================================================
                    ACCOUNT INFORMATION
                    ================================================= */}

                <div className="profile-section">

                  <div className="profile-section-title">

                    <span>
                      01
                    </span>

                    <div>

                      <h2>
                        Account Information
                      </h2>

                      <p>
                        Your PARAM Play Store account details.
                      </p>

                    </div>

                  </div>


                  <div className="profile-grid">

                    <div className="profile-field">

                      <span>
                        Full Name
                      </span>

                      <strong>
                        {user.full_name ||
                          "—"}
                      </strong>

                    </div>


                    <div className="profile-field">

                      <span>
                        Email
                      </span>

                      <strong>
                        {user.email ||
                          "—"}
                      </strong>

                    </div>


                    <div className="profile-field">

                      <span>
                        Account Type
                      </span>

                      <strong>
                        {user.is_developer
                          ? "Developer"
                          : "User"}
                      </strong>

                    </div>


                    <div className="profile-field">

                      <span>
                        Developer Type
                      </span>

                      <strong>
                        {user.developer_type ||
                          "—"}
                      </strong>

                    </div>

                  </div>

                </div>


                {/* =================================================
                    DEVELOPER STATUS
                    ================================================= */}

                <div className="profile-section">

                  <div className="profile-section-title">

                    <span>
                      02
                    </span>

                    <div>

                      <h2>
                        Developer Status
                      </h2>

                      <p>
                        Developer account verification
                        and access status.
                      </p>

                    </div>

                  </div>


                  <div className="profile-status-grid">

                    <div className="profile-status-item">

                      <span>
                        Developer
                      </span>

                      <strong>
                        {user.is_developer
                          ? "Active Developer"
                          : "Regular User"}
                      </strong>

                    </div>


                    <div className="profile-status-item">

                      <span>
                        Developer Active
                      </span>

                      <strong>
                        {user.developer_active
                          ? "Active"
                          : "Inactive"}
                      </strong>

                    </div>


                    <div className="profile-status-item">

                      <span>
                        Plan
                      </span>

                      <strong>
                        {user.developer_plan ||
                          "—"}
                      </strong>

                    </div>


                    <div className="profile-status-item">

                      <span>
                        Payment / Review
                      </span>

                      <strong>
                        {user.payment_status ||
                          "—"}
                      </strong>

                    </div>

                  </div>

                </div>


                {/* =================================================
                    CONTACT INFORMATION
                    ================================================= */}

                <div className="profile-section">

                  <div className="profile-section-title">

                    <span>
                      03
                    </span>

                    <div>

                      <h2>
                        Contact Information
                      </h2>

                      <p>
                        Developer contact information.
                      </p>

                    </div>

                  </div>


                  <div className="profile-grid">

                    <div className="profile-field">

                      <span>
                        Country
                      </span>

                      <strong>
                        {user.country ||
                          "—"}
                      </strong>

                    </div>


                    <div className="profile-field">

                      <span>
                        Phone
                      </span>

                      <strong>
                        {user.phone ||
                          "—"}
                      </strong>

                    </div>


                    <div className="profile-field">

                      <span>
                        Company
                      </span>

                      <strong>
                        {user.company_name ||
                          "—"}
                      </strong>

                    </div>


                    <div className="profile-field">

                      <span>
                        Website
                      </span>

                      <strong>
                        {user.website ||
                          "—"}
                      </strong>

                    </div>


                    <div className="profile-field">

                      <span>
                        GitHub
                      </span>

                      <strong>
                        {user.github ||
                          "—"}
                      </strong>

                    </div>

                  </div>


                  <div className="profile-address">

                    <span>
                      Address
                    </span>

                    <p>
                      {user.address ||
                        "No address added yet."}
                    </p>

                  </div>


                  {user.bio && (

                    <div className="profile-address">

                      <span>
                        Bio
                      </span>

                      <p>
                        {user.bio}
                      </p>

                    </div>

                  )}

                </div>


                {/* =================================================
                    ACTIONS
                    ================================================= */}

                <div className="profile-actions">

                  {user.is_developer && (

                    <button
                      type="button"
                      className="primary-button"
                      onClick={handleDashboard}
                    >
                      Developer Dashboard
                    </button>

                  )}


                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() =>
                      navigate("/")
                    }
                  >
                    Browse Marketplace
                  </button>


                  <button
                    type="button"
                    className="refresh-button"
                    onClick={handleLogout}
                  >
                    Logout
                  </button>

                </div>

              </div>

            )}

        </section>

      </main>


      {/* =================================================
          FOOTER
          ================================================= */}

      <footer className="footer">

        <span>
          PARAM Play Store
        </span>

        <span>
          Developer-friendly app marketplace
        </span>

      </footer>

    </div>
  );
}


export default Profile;


