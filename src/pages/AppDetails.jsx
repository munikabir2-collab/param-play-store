import { useEffect, useState } from "react";

import {
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  getAppDetails,
  getDownloadUrl,
} from "../api/client";


function AppDetails() {

  const { appId } = useParams();

  const navigate = useNavigate();

  const [app, setApp] = useState(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  useEffect(() => {

    const loadAppDetails = async () => {

      try {

        setLoading(true);
        setError("");

        const data =
          await getAppDetails(appId);

        setApp(data);

      } catch (err) {

        console.error(
          "App details error:",
          err
        );

        setError(
          err.response?.data?.detail ||
          err.message ||
          "App details load nahi ho payi"
        );

      } finally {

        setLoading(false);

      }

    };


    if (appId) {
      loadAppDetails();
    }

  }, [appId]);


  const formatSize = (sizeMb) => {

    if (
      sizeMb === null ||
      sizeMb === undefined
    ) {
      return "Size unavailable";
    }

    return `${Number(sizeMb).toFixed(2)} MB`;

  };


  const formatFileType = (fileType) => {

    if (fileType === ".aab") {
      return "AAB → APK";
    }

    return "APK";

  };


  const formatDate = (dateValue) => {

    if (!dateValue) {
      return "Not available";
    }

    const date =
      new Date(dateValue);

    if (Number.isNaN(date.getTime())) {
      return "Not available";
    }

    return date.toLocaleString();

  };


  // =====================================================
  // LOADING
  // =====================================================

  if (loading) {

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

        </header>


        <main className="container">

          <div className="state-card">
            App details load हो रही हैं...
          </div>

        </main>

      </div>
    );

  }


  // =====================================================
  // ERROR
  // =====================================================

  if (error) {

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

        </header>


        <main className="container">

          <div className="error-card">

            <strong>
              App Details Error
            </strong>

            <p>
              {error}
            </p>


            <button
              className="retry-button"
              onClick={() =>
                navigate("/")
              }
            >
              Back to Marketplace
            </button>

          </div>

        </main>

      </div>
    );

  }


  // =====================================================
  // APP NOT FOUND
  // =====================================================

  if (!app) {

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

        </header>


        <main className="container">

          <div className="state-card">

            App नहीं मिली।

            <br />

            <button
              className="retry-button"
              onClick={() =>
                navigate("/")
              }
            >
              Back to Marketplace
            </button>

          </div>

        </main>

      </div>
    );

  }


  // =====================================================
  // APP INITIAL
  // =====================================================

  const initial =
    app.app_name
      ?.charAt(0)
      ?.toUpperCase() || "A";


  // =====================================================
  // MAIN PAGE
  // =====================================================

  return (
    <div className="page">

      {/* =================================================
          HEADER
          ================================================= */}

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
          className="refresh-button"
          onClick={() =>
            navigate("/")
          }
        >
          Marketplace
        </button>

      </header>


      {/* =================================================
          MAIN
          ================================================= */}

      <main className="container">

        <button
          className="back-button"
          onClick={() =>
            navigate(-1)
          }
        >
          ← Back
        </button>


        <section className="details-card">

          {/* =============================================
              APP HEADER
              ============================================= */}

          <div className="details-header">

            <div className="details-icon">

              {app.icon_path ? (

                <img
                  src={app.icon_path}
                  alt={app.app_name}
                />

              ) : (

                initial

              )}

            </div>


            <div className="details-title">

              <p className="eyebrow">
                APP DETAILS
              </p>

              <h1>
                {app.app_name}
              </h1>

              <p className="details-version">
                Version {app.version}
              </p>

            </div>

          </div>


          {/* =============================================
              APP META
              ============================================= */}

          <div className="details-meta">

            <div className="details-meta-item">

              <span>
                Type
              </span>

              <strong>
                {formatFileType(
                  app.file_type
                )}
              </strong>

            </div>


            <div className="details-meta-item">

              <span>
                Size
              </span>

              <strong>
                {formatSize(
                  app.size_mb
                )}
              </strong>

            </div>


            <div className="details-meta-item">

              <span>
                Category
              </span>

              <strong>
                {app.category ||
                  "Other"}
              </strong>

            </div>


            <div className="details-meta-item">

              <span>
                Developer
              </span>

              <strong>
                {app.developer_id
                  ? `Developer #${app.developer_id}`
                  : "Not specified"}
              </strong>

            </div>

          </div>


          {/* =============================================
              DESCRIPTION
              ============================================= */}

          <section className="details-section">

            <h2>
              Description
            </h2>

            <p>

              {app.description?.trim()
                ? app.description
                : "इस app के लिए अभी कोई description उपलब्ध नहीं है।"}

            </p>

          </section>


          {/* =============================================
              RELEASE INFORMATION
              ============================================= */}

          <section className="details-section">

            <h2>
              Release Information
            </h2>


            <div className="release-info">

              <div>

                <span>
                  Version
                </span>

                <strong>
                  {app.version}
                </strong>

              </div>


              <div>

                <span>
                  Package Type
                </span>

                <strong>
                  {formatFileType(
                    app.file_type
                  )}
                </strong>

              </div>


              <div>

                <span>
                  Published
                </span>

                <strong>
                  {formatDate(
                    app.created_at
                  )}
                </strong>

              </div>

            </div>

          </section>


          {/* =============================================
              ACTIONS
              ============================================= */}

          <div className="details-actions">

            <a
              className="download-button"
              href={getDownloadUrl(
                app.id
              )}
            >
              Download APK
            </a>


            <button
              className="back-button"
              onClick={() =>
                navigate("/")
              }
            >
              Back to Marketplace
            </button>

          </div>

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


export default AppDetails;