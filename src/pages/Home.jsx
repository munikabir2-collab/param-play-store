import { useEffect, useState } from "react";

import {
  getApps,
  getDownloadUrl,
} from "../api/client";

import {
  Link,
  useNavigate,
} from "react-router-dom";


function Home() {
  const navigate = useNavigate();

  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


  const loadApps = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getApps();

      setApps(data.apps || []);
    } catch (err) {
      console.error(
        "Backend connection error:",
        err
      );

      setError(
        err.response?.data?.detail ||
          err.message ||
          "Backend se connection nahi ho paya"
      );
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    loadApps();
  }, []);


  const formatSize = (sizeMb) => {
    if (
      sizeMb === null ||
      sizeMb === undefined
    ) {
      return "Size unavailable";
    }

    return `${Number(sizeMb).toFixed(2)} MB`;
  };


  const getIconUrl = (app) => {
    if (!app?.icon_url) {
      return null;
    }

    if (
      app.icon_url.startsWith("http://") ||
      app.icon_url.startsWith("https://")
    ) {
      return app.icon_url;
    }

    return `http://127.0.0.1:8000${app.icon_url}`;
  };


  return (
    <div className="page">

      {/* =================================================
          TOP BAR
          ================================================= */}

      <header className="topbar">

        <div>

          <div className="brand">
            🇮🇳 PARAM Play Store
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

          {/* USER PROFILE */}

          <button
            type="button"
            className="refresh-button"
            onClick={() =>
              navigate("/profile")
            }
          >
            User Profile
          </button>


          {/* DEVELOPER LOGIN */}

          <button
            type="button"
            className="refresh-button"
            onClick={() =>
              navigate("/login")
            }
          >
            Developer Login
          </button>


          {/* CREATE ACCOUNT */}

          <button
            type="button"
            className="download-button"
            style={{
              width: "auto",
              whiteSpace: "nowrap",
            }}
            onClick={() =>
              navigate("/signup")
            }
          >
            Create Account
          </button>


          {/* REFRESH */}

          <button
            type="button"
            className="refresh-button"
            onClick={loadApps}
            disabled={loading}
          >
            {loading
              ? "Loading..."
              : "Refresh"}
          </button>

        </div>

      </header>


      <main className="container">

        {/* =================================================
            HERO
            ================================================= */}

        <section className="hero">

          <div>

            <p className="eyebrow">
              APP MARKETPLACE
            </p>

            <h1>
              Discover and test Android apps
            </h1>

            <p className="hero-text">
              APK और AAB uploads से बने
              installable Android apps को एक
              जगह देखें और download करें।
            </p>

          </div>


          <div className="hero-stat">

            <strong>
              {apps.length}
            </strong>

            <span>
              Available Apps
            </span>

          </div>

        </section>


        {/* =================================================
            LOADING
            ================================================= */}

        {loading && (
          <div className="state-card">
            Apps load हो रहे हैं...
          </div>
        )}


        {/* =================================================
            ERROR
            ================================================= */}

        {error && (
          <div className="error-card">

            <strong>
              Backend Error
            </strong>

            <p>
              {error}
            </p>

            <button
              type="button"
              onClick={loadApps}
              className="retry-button"
            >
              Try Again
            </button>

          </div>
        )}


        {/* =================================================
            EMPTY
            ================================================= */}

        {!loading &&
          !error &&
          apps.length === 0 && (

            <div className="state-card">
              अभी कोई app उपलब्ध नहीं है।
            </div>

          )}


        {/* =================================================
            APPS
            ================================================= */}

        {!loading &&
          !error &&
          apps.length > 0 && (

            <section className="apps-section">

              <div className="section-heading">

                <div>

                  <p className="eyebrow">
                    AVAILABLE APPS
                  </p>

                  <h2>
                    Explore Apps
                  </h2>

                </div>

                <span className="app-count">
                  {apps.length} apps
                </span>

              </div>


              <div className="app-grid">

                {apps.map((app) => {

                  const iconUrl =
                    getIconUrl(app);

                  return (
                    <article
                      className="app-card"
                      key={app.id}
                    >

                      {/* APP ICON */}

                      <div className="app-icon">

                        {iconUrl ? (
                          <img
                            src={iconUrl}
                            alt={`${app.app_name} icon`}
                            onError={(event) => {
                              event.currentTarget.style.display =
                                "none";
                            }}
                          />
                        ) : (
                          app.app_name
                            ?.charAt(0)
                            ?.toUpperCase() || "A"
                        )}

                      </div>


                      {/* APP CONTENT */}

                      <div className="app-content">

                        <h3>
                          {app.app_name}
                        </h3>


                        <p className="version">
                          Version {app.version}
                        </p>


                        <div className="app-meta">

                          <span>
                            {formatSize(
                              app.size_mb
                            )}
                          </span>

                          <span className="meta-separator">
                            •
                          </span>

                          <span>
                            {app.file_type === ".aab"
                              ? "AAB → APK"
                              : "APK"}
                          </span>

                        </div>


                        {app.description && (
                          <p className="app-description">
                            {app.description}
                          </p>
                        )}


                        <div className="app-actions">

                          <Link
                            className="details-button"
                            to={`/apps/${app.id}`}
                          >
                            View Details
                          </Link>


                          <a
                            className="download-button"
                            href={getDownloadUrl(
                              app.id
                            )}
                          >
                            Download APK
                          </a>

                        </div>

                      </div>

                    </article>
                  );
                })}

              </div>

            </section>

          )}

      </main>


      {/* =================================================
          FOOTER
          ================================================= */}

      <footer className="footer">

        <span>
          🇮🇳 PARAM Play Store
        </span>

      </footer>

    </div>
  );
}


export default Home;
