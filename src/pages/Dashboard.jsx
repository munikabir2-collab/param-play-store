import { useEffect, useMemo, useState } from "react";

import { useNavigate } from "react-router-dom";

import {
  uploadApp,
  getMyApps,
  getDownloadUrl,
  updateApp,
  deleteApp,
  getMyDeveloperProfile,
  updateMyDeveloperProfile,
  getDeveloperPaymentStatus,
} from "../api/client";

const CATEGORIES = [
  "Other",
  "Education",
  "Business",
  "Productivity",
  "Entertainment",
  "Health",
  "Finance",
  "Tools",
  "Games",
  "Social",
  "Communication",
];

const ICON_EXTENSIONS = [
  ".png",
  ".jpg",
  ".jpeg",
  ".webp",
  ".svg",
];

const isAndroidPackageName = (value) => {
  return /^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+$/.test(
    value.trim()
  );
};

const isAndroidFile = (file) => {
  if (!file) return false;

  const name = file.name.toLowerCase();

  return (
    name.endsWith(".apk") ||
    name.endsWith(".aab")
  );
};

const isIconFile = (file) => {
  if (!file) return true;

  const name = file.name.toLowerCase();

  return ICON_EXTENSIONS.some((extension) =>
    name.endsWith(extension)
  );
};

function Dashboard() {
  const navigate = useNavigate();

  // =======================================================
  // UPLOAD STATE
  // =======================================================

  const [appName, setAppName] = useState("");
  const [packageName, setPackageName] = useState("");
  const [version, setVersion] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("Other");
  const [changelog, setChangelog] = useState("");
  const [file, setFile] = useState(null);
  const [icon, setIcon] = useState(null);

  // =======================================================
  // APPS STATE
  // =======================================================

  const [apps, setApps] = useState([]);

  const [loading, setLoading] = useState(false);
  const [appsLoading, setAppsLoading] = useState(true);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  // =======================================================
  // DEVELOPER PROFILE STATE
  // =======================================================

  const [developerProfile, setDeveloperProfile] =
    useState(null);

  const [profileLoading, setProfileLoading] =
    useState(true);

  const [profileSaving, setProfileSaving] =
    useState(false);

  const [profileEditing, setProfileEditing] =
    useState(false);

  const [profileError, setProfileError] =
    useState("");

  const [profileMessage, setProfileMessage] =
    useState("");

  const [profileForm, setProfileForm] = useState({
    full_name: "",
    developer_type: "individual",
    country: "",
    phone: "",
    address: "",
    company_name: "",
    bio: "",
    website: "",
    github: "",
  });

  // =======================================================
  // PAYMENT STATE
  // =======================================================

  const [paymentStatus, setPaymentStatus] =
    useState(null);

  const [paymentLoading, setPaymentLoading] =
    useState(true);

  const [paymentError, setPaymentError] =
    useState("");

  // =======================================================
  // UPDATE STATE
  // =======================================================

  const [editingAppId, setEditingAppId] =
    useState(null);

  const [updateVersion, setUpdateVersion] =
    useState("");

  const [updatePackageName, setUpdatePackageName] =
    useState("");

  const [updateDescription, setUpdateDescription] =
    useState("");

  const [updateCategory, setUpdateCategory] =
    useState("Other");

  const [updateChangelog, setUpdateChangelog] =
    useState("");

  const [updateFile, setUpdateFile] =
    useState(null);

  const [updateIcon, setUpdateIcon] =
    useState(null);

  const [updateLoading, setUpdateLoading] =
    useState(false);

  // =======================================================
  // DELETE STATE
  // =======================================================

  const [deletingAppId, setDeletingAppId] =
    useState(null);

  // =======================================================
  // LOGIN + INITIAL LOAD
  // =======================================================

  useEffect(() => {
    const token =
      localStorage.getItem(
        "PARAM Play Store_token"
      );

    if (!token) {
      navigate("/login");
      return;
    }

    loadMyApps();
    loadDeveloperProfile();
    loadPaymentStatus();
  }, [navigate]);

  // =======================================================
  // LOAD MY APPS
  // =======================================================

  const loadMyApps = async () => {
    try {
      setAppsLoading(true);
      setError("");

      const token =
        localStorage.getItem(
          "PARAM Play Store_token"
        );

      if (!token) {
        navigate("/login");
        return;
      }

      const data =
        await getMyApps(token);

      setApps(
        data.apps || []
      );
    } catch (err) {
      console.error(
        "My apps loading error:",
        err
      );

      if (
        err.response?.status === 401
      ) {
        localStorage.removeItem(
          "PARAM Play Store_token"
        );

        navigate("/login");
        return;
      }

      setError(
        err.response?.data?.detail ||
          err.message ||
          "Apps load nahi ho paye."
      );
    } finally {
      setAppsLoading(false);
    }
  };

  // =======================================================
  // LOAD DEVELOPER PROFILE
  // =======================================================

  const loadDeveloperProfile = async () => {
    try {
      setProfileLoading(true);
      setProfileError("");

      const token =
        localStorage.getItem(
          "PARAM Play Store_token"
        );

      if (!token) {
        navigate("/login");
        return;
      }

      const data =
        await getMyDeveloperProfile(
          token
        );

      setDeveloperProfile(data);

      setProfileForm({
        full_name:
          data.full_name || "",

        developer_type:
          data.developer_type ||
          "individual",

        country:
          data.country || "",

        phone:
          data.phone || "",

        address:
          data.address || "",

        company_name:
          data.company_name || "",

        bio:
          data.bio || "",

        website:
          data.website || "",

        github:
          data.github || "",
      });
    } catch (err) {
      console.error(
        "Developer profile loading error:",
        err
      );

      if (
        err.response?.status === 401
      ) {
        localStorage.removeItem(
          "PARAM Play Store_token"
        );

        navigate("/login");
        return;
      }

      setProfileError(
        err.response?.data?.detail ||
          err.message ||
          "Developer profile load nahi ho paya."
      );
    } finally {
      setProfileLoading(false);
    }
  };

  // =======================================================
  // LOAD PAYMENT STATUS
  // =======================================================

  const loadPaymentStatus = async () => {
    try {
      setPaymentLoading(true);
      setPaymentError("");

      const token =
        localStorage.getItem(
          "PARAM Play Store_token"
        );

      if (!token) {
        navigate("/login");
        return;
      }

      const data =
        await getDeveloperPaymentStatus(
          token
        );

      setPaymentStatus(data);
    } catch (err) {
      console.error(
        "Developer payment status error:",
        err
      );

      if (
        err.response?.status === 401
      ) {
        localStorage.removeItem(
          "PARAM Play Store_token"
        );

        navigate("/login");
        return;
      }

      setPaymentError(
        err.response?.data?.detail ||
          err.message ||
          "Payment status load nahi ho paya."
      );
    } finally {
      setPaymentLoading(false);
    }
  };

  // =======================================================
  // PROFILE INPUT
  // =======================================================

  const handleProfileChange = (
    event
  ) => {
    const {
      name,
      value,
    } = event.target;

    setProfileForm(
      (previous) => ({
        ...previous,
        [name]: value,
      })
    );
  };

  // =======================================================
  // SAVE DEVELOPER PROFILE
  // =======================================================

  const handleProfileSave = async (
    event
  ) => {
    event.preventDefault();

    setProfileError("");
    setProfileMessage("");

    const token =
      localStorage.getItem(
        "PARAM Play Store_token"
      );

    if (!token) {
      navigate("/login");
      return;
    }

    const cleanProfile = {
      full_name:
        profileForm.full_name.trim(),

      developer_type:
        profileForm.developer_type,

      country:
        profileForm.country.trim(),

      phone:
        profileForm.phone.trim(),

      address:
        profileForm.address.trim(),

      company_name:
        profileForm.company_name.trim(),

      bio:
        profileForm.bio.trim(),

      website:
        profileForm.website.trim(),

      github:
        profileForm.github.trim(),
    };

    if (!cleanProfile.full_name) {
      setProfileError(
        "Full name required hai."
      );
      return;
    }

    if (!cleanProfile.country) {
      setProfileError(
        "Country required hai."
      );
      return;
    }

    if (!cleanProfile.phone) {
      setProfileError(
        "Phone number required hai."
      );
      return;
    }

    if (!cleanProfile.address) {
      setProfileError(
        "Address required hai."
      );
      return;
    }

    try {
      setProfileSaving(true);

      const data =
        await updateMyDeveloperProfile(
          cleanProfile,
          token
        );

      setDeveloperProfile(data);

      setProfileForm({
        full_name:
          data.full_name || "",

        developer_type:
          data.developer_type ||
          "individual",

        country:
          data.country || "",

        phone:
          data.phone || "",

        address:
          data.address || "",

        company_name:
          data.company_name || "",

        bio:
          data.bio || "",

        website:
          data.website || "",

        github:
          data.github || "",
      });

      setProfileEditing(false);

      setProfileMessage(
        "Developer profile successfully save ho gaya."
      );
    } catch (err) {
      console.error(
        "Developer profile save error:",
        err
      );

      if (
        err.response?.status === 401
      ) {
        localStorage.removeItem(
          "PARAM Play Store_token"
        );

        navigate("/login");
        return;
      }

      setProfileError(
        err.response?.data?.detail ||
          err.message ||
          "Developer profile save nahi ho paya."
      );
    } finally {
      setProfileSaving(false);
    }
  };

  // =======================================================
  // CANCEL PROFILE EDIT
  // =======================================================

  const handleCancelProfileEdit = () => {
    if (developerProfile) {
      setProfileForm({
        full_name:
          developerProfile.full_name ||
          "",

        developer_type:
          developerProfile.developer_type ||
          "individual",

        country:
          developerProfile.country ||
          "",

        phone:
          developerProfile.phone ||
          "",

        address:
          developerProfile.address ||
          "",

        company_name:
          developerProfile.company_name ||
          "",

        bio:
          developerProfile.bio ||
          "",

        website:
          developerProfile.website ||
          "",

        github:
          developerProfile.github ||
          "",
      });
    }

    setProfileError("");
    setProfileMessage("");
    setProfileEditing(false);
  };

  // =======================================================
  // PROFILE STATUS
  // =======================================================

  const developerStatus =
    developerProfile?.payment_status ||
    "unknown";

  const developerPlan =
    developerProfile?.developer_plan ||
    "free";

  const developerActive =
    Boolean(
      developerProfile?.developer_active
    );

  // =======================================================
  // PAYMENT STATUS HELPERS
  // =======================================================

  const paymentRequired =
    Boolean(
      paymentStatus?.payment_required
    );

  const paymentState =
    paymentStatus?.payment_status ||
    developerStatus ||
    "unknown";

  const paymentAmount =
    paymentStatus?.amount ||
    "999.00";

  const paymentCurrency =
    paymentStatus?.currency ||
    "INR";

  const handleOpenPayment = () => {
    navigate(
      "/developer/payment"
    );
  };

  // =======================================================
  // UPLOAD FILE
  // =======================================================

  const handleFileChange = (
    event
  ) => {
    const selectedFile =
      event.target.files?.[0] ||
      null;

    setFile(selectedFile);
    setMessage("");
    setError("");
  };

  // =======================================================
  // ICON FILE
  // =======================================================

  const handleIconChange = (
    event
  ) => {
    const selectedIcon =
      event.target.files?.[0] ||
      null;

    setIcon(selectedIcon);
    setMessage("");
    setError("");
  };

  // =======================================================
  // UPLOAD APP
  // =======================================================

  const handleUpload = async (
    event
  ) => {
    event.preventDefault();

    setMessage("");
    setError("");

    if (!developerActive) {
      setError(
        "Developer account active hone ke baad hi app upload kar sakte hain."
      );
      return;
    }

    const cleanAppName =
      appName.trim();

    const cleanPackageName =
      packageName.trim();

    const cleanVersion =
      version.trim();

    if (!cleanAppName) {
      setError(
        "App name required hai."
      );
      return;
    }

    if (!cleanPackageName) {
      setError(
        "Package name required hai."
      );
      return;
    }

    if (
      !isAndroidPackageName(
        cleanPackageName
      )
    ) {
      setError(
        "Valid Android package name enter karein. Example: com.example.myapp"
      );
      return;
    }

    if (!cleanVersion) {
      setError(
        "Version required hai."
      );
      return;
    }

    if (!file) {
      setError(
        "APK ya AAB file select karein."
      );
      return;
    }

    if (!isAndroidFile(file)) {
      setError(
        "Sirf APK ya AAB file allowed hai."
      );
      return;
    }

    if (!isIconFile(icon)) {
      setError(
        "App icon PNG, JPG, JPEG, WEBP ya SVG hona chahiye."
      );
      return;
    }

    const token =
      localStorage.getItem(
        "PARAM Play Store_token"
      );

    if (!token) {
      navigate("/login");
      return;
    }

    try {
      setLoading(true);

      const result =
        await uploadApp(
          cleanAppName,
          cleanPackageName,
          cleanVersion,
          file,
          token,
          description.trim(),
          category,
          changelog.trim(),
          icon
        );

      setMessage(
        result.message ||
          "App successfully upload ho gaya."
      );

      setAppName("");
      setPackageName("");
      setVersion("");
      setDescription("");
      setCategory("Other");
      setChangelog("");
      setFile(null);
      setIcon(null);

      const fileInput =
        document.getElementById(
          "app-file"
        );

      if (fileInput) {
        fileInput.value = "";
      }

      const iconInput =
        document.getElementById(
          "app-icon"
        );

      if (iconInput) {
        iconInput.value = "";
      }

      await loadMyApps();
    } catch (err) {
      console.error(
        "App upload error:",
        err
      );

      if (
        err.response?.status === 401
      ) {
        localStorage.removeItem(
          "PARAM Play Store_token"
        );

        navigate("/login");
        return;
      }

      setError(
        err.response?.data?.detail ||
          err.message ||
          "App upload nahi ho paya."
      );
    } finally {
      setLoading(false);
    }
  };

  // =======================================================
  // START UPDATE
  // =======================================================

  const handleStartUpdate = (
    app
  ) => {
    if (!developerActive) {
      setError(
        "Developer account active nahi hai."
      );
      return;
    }

    setMessage("");
    setError("");

    setEditingAppId(app.id);

    setUpdateVersion(
      app.version || ""
    );

    setUpdatePackageName(
      app.package_name || ""
    );

    setUpdateDescription(
      app.description || ""
    );

    setUpdateCategory(
      app.category || "Other"
    );

    setUpdateChangelog(
      app.changelog || ""
    );

    setUpdateFile(null);
    setUpdateIcon(null);
  };

  // =======================================================
  // CANCEL UPDATE
  // =======================================================

  const handleCancelUpdate = () => {
    setEditingAppId(null);

    setUpdateVersion("");
    setUpdatePackageName("");
    setUpdateDescription("");
    setUpdateCategory("Other");
    setUpdateChangelog("");
    setUpdateFile(null);
    setUpdateIcon(null);
  };

  // =======================================================
  // UPDATE FILE
  // =======================================================

  const handleUpdateFileChange = (
    event
  ) => {
    const selectedFile =
      event.target.files?.[0] ||
      null;

    setUpdateFile(selectedFile);

    setMessage("");
    setError("");
  };

  // =======================================================
  // UPDATE ICON
  // =======================================================

  const handleUpdateIconChange = (
    event
  ) => {
    const selectedIcon =
      event.target.files?.[0] ||
      null;

    setUpdateIcon(selectedIcon);

    setMessage("");
    setError("");
  };

  // =======================================================
  // UPDATE APP
  // =======================================================

  const handleUpdate = async (
    event,
    appId
  ) => {
    event.preventDefault();

    setMessage("");
    setError("");

    if (!developerActive) {
      setError(
        "Developer account active hone ke baad hi app update kar sakte hain."
      );
      return;
    }

    const cleanVersion =
      updateVersion.trim();

    const cleanPackageName =
      updatePackageName.trim();

    if (!cleanVersion) {
      setError(
        "Update version required hai."
      );
      return;
    }

    if (
      cleanPackageName &&
      !isAndroidPackageName(
        cleanPackageName
      )
    ) {
      setError(
        "Valid Android package name enter karein."
      );
      return;
    }

    if (!updateFile) {
      setError(
        "Nayi APK ya AAB file select karein."
      );
      return;
    }

    if (!isAndroidFile(updateFile)) {
      setError(
        "Sirf APK ya AAB file allowed hai."
      );
      return;
    }

    if (!isIconFile(updateIcon)) {
      setError(
        "App icon PNG, JPG, JPEG, WEBP ya SVG hona chahiye."
      );
      return;
    }

    const token =
      localStorage.getItem(
        "PARAM Play Store_token"
      );

    if (!token) {
      navigate("/login");
      return;
    }

    try {
      setUpdateLoading(true);

      const result =
        await updateApp(
          appId,
          cleanVersion,
          updateFile,
          token,
          cleanPackageName,
          updateDescription.trim(),
          updateCategory,
          updateChangelog.trim(),
          updateIcon
        );

      setMessage(
        result.message ||
          "App successfully update ho gaya."
      );

      handleCancelUpdate();

      await loadMyApps();
    } catch (err) {
      console.error(
        "App update error:",
        err
      );

      if (
        err.response?.status === 401
      ) {
        localStorage.removeItem(
          "PARAM Play Store_token"
        );

        navigate("/login");
        return;
      }

      setError(
        err.response?.data?.detail ||
          err.message ||
          "App update nahi ho paya."
      );
    } finally {
      setUpdateLoading(false);
    }
  };

  // =======================================================
  // DELETE APP
  // =======================================================

  const handleDelete = async (
    app
  ) => {
    if (!developerActive) {
      setError(
        "Developer account active nahi hai."
      );
      return;
    }

    const confirmed =
      window.confirm(
        `Kya aap "${app.app_name}" ko permanently delete karna chahte hain?\n\nIsse app database aur stored file se remove ho jayega.`
      );

    if (!confirmed) {
      return;
    }

    setMessage("");
    setError("");

    const token =
      localStorage.getItem(
        "PARAM Play Store_token"
      );

    if (!token) {
      navigate("/login");
      return;
    }

    try {
      setDeletingAppId(app.id);

      const result =
        await deleteApp(
          app.id,
          token
        );

      setMessage(
        result.message ||
          "App successfully delete ho gaya."
      );

      if (
        editingAppId === app.id
      ) {
        handleCancelUpdate();
      }

      await loadMyApps();
    } catch (err) {
      console.error(
        "App delete error:",
        err
      );

      if (
        err.response?.status === 401
      ) {
        localStorage.removeItem(
          "PARAM Play Store_token"
        );

        navigate("/login");
        return;
      }

      setError(
        err.response?.data?.detail ||
          err.message ||
          "App delete nahi ho paya."
      );
    } finally {
      setDeletingAppId(null);
    }
  };

  // =======================================================
  // LOGOUT
  // =======================================================

  const handleLogout = () => {
    localStorage.removeItem(
      "PARAM Play Store_token"
    );

    navigate("/login");
  };

  // =======================================================
  // FORMAT HELPERS
  // =======================================================

  const formatSize = (
    sizeMb
  ) => {
    if (
      sizeMb === null ||
      sizeMb === undefined
    ) {
      return "Size unavailable";
    }

    return `${Number(
      sizeMb
    ).toFixed(2)} MB`;
  };

  const formatFileType = (
    fileType
  ) => {
    if (
      fileType === ".aab"
    ) {
      return "AAB → APK";
    }

    return "APK";
  };

  // =======================================================
  // DASHBOARD STATS
  // =======================================================

  const dashboardStats =
    useMemo(() => {
      const downloads =
        apps.reduce(
          (
            total,
            app
          ) =>
            total +
            Number(
              app.download_count ||
                0
            ),
          0
        );

      const views =
        apps.reduce(
          (
            total,
            app
          ) =>
            total +
            Number(
              app.view_count ||
                0
            ),
          0
        );

      const ratings =
        apps
          .map((app) =>
            Number(
              app.rating || 0
            )
          )
          .filter(
            (rating) =>
              rating > 0
          );

      const averageRating =
        ratings.length > 0
          ? ratings.reduce(
              (
                sum,
                rating
              ) =>
                sum + rating,
              0
            ) /
            ratings.length
          : 0;

      return {
        downloads,
        views,
        averageRating,
      };
    }, [apps]);

  // =======================================================
  // UI
  // =======================================================

  return (
    <div className="page dashboard-page">

      {/* ===================================================
          HEADER
      =================================================== */}

      <header className="topbar dashboard-topbar">

        <div className="brand-area">

          <div className="brand">
            PARAM Play Store
          </div>

          <div className="subtitle">
            Developer Dashboard
          </div>

        </div>

        <div className="topbar-actions">

          <button
            type="button"
            className="refresh-button"
            onClick={() => {
              loadMyApps();
              loadDeveloperProfile();
              loadPaymentStatus();
            }}
            disabled={
              appsLoading ||
              profileLoading ||
              paymentLoading
            }
          >
            {appsLoading ||
            profileLoading ||
            paymentLoading
              ? "Loading..."
              : "Refresh"}
          </button>

          <button
            type="button"
            className="logout-button"
            onClick={handleLogout}
          >
            Logout
          </button>

        </div>

      </header>

      <main className="container dashboard-container">

        {/* =================================================
            HERO
        ================================================= */}

        <section className="dashboard-hero">

          <div className="dashboard-hero-content">

            <span className="hero-badge">
              DEVELOPER DASHBOARD
            </span>

            <h1>
              Manage your Android apps
            </h1>

            <p>
              APK और AAB applications upload
              करें, versions manage करें और
              अपने apps की performance
              statistics देखें।
            </p>

            <div className="hero-actions">

              {developerActive ? (
                <a
                  href="#upload-app"
                  className="primary-action"
                >
                  + Upload New App
                </a>
              ) : paymentRequired ? (
                <button
                  type="button"
                  className="primary-action"
                  onClick={
                    handleOpenPayment
                  }
                >
                  Pay ₹{paymentAmount}
                </button>
              ) : (
                <a
                  href="#developer-profile"
                  className="primary-action"
                >
                  View Developer Status
                </a>
              )}

              <a
                href="#your-apps"
                className="secondary-action"
              >
                View My Apps
              </a>

            </div>

          </div>

          <div className="hero-stat-card">

            <div className="hero-stat-label">
              Published Apps
            </div>

            <strong>
              {apps.length}
            </strong>

            <span>
              Apps in your account
            </span>

          </div>

        </section>

        {/* =================================================
            PAYMENT / DEVELOPER STATUS
        ================================================= */}

        <section
          className="dashboard-section"
          id="developer-payment-status"
        >

          <div className="section-title">

            <div>

              <span className="section-kicker">
                DEVELOPER STATUS
              </span>

              <h2>
                Account & payment status
              </h2>

              <p>
                Developer registration, payment
                and verification status.
              </p>

            </div>

          </div>

          {paymentLoading ? (

            <div className="state-card professional-state">

              <div className="loading-spinner" />

              <div>

                <strong>
                  Loading payment status
                </strong>

                <p>
                  Please wait...
                </p>

              </div>

            </div>

          ) : paymentError ? (

            <div className="alert alert-error">

              <div className="alert-icon">
                !
              </div>

              <div>

                <strong>
                  Payment status error
                </strong>

                <p>
                  {paymentError}
                </p>

                <button
                  type="button"
                  className="secondary-button"
                  onClick={
                    loadPaymentStatus
                  }
                >
                  Retry
                </button>

              </div>

            </div>

          ) : (

            <div className="developer-profile-card">

              <div className="developer-profile-status-grid">

                <div className="profile-status-item">

                  <span>
                    Account
                  </span>

                  <strong>
                    {developerActive
                      ? "Developer Active"
                      : "Not Active"}
                  </strong>

                </div>

                <div className="profile-status-item">

                  <span>
                    Plan
                  </span>

                  <strong>
                    {developerPlan}
                  </strong>

                </div>

                <div className="profile-status-item">

                  <span>
                    Payment
                  </span>

                  <strong>
                    {paymentState}
                  </strong>

                </div>

                <div className="profile-status-item">

                  <span>
                    Amount
                  </span>

                  <strong>
                    ₹{paymentAmount}
                  </strong>

                </div>

              </div>

              {paymentRequired && (
                <div
                  className="alert alert-error"
                  style={{
                    marginTop: "20px",
                  }}
                >

                  <div className="alert-icon">
                    !
                  </div>

                  <div>

                    <strong>
                      Developer payment required
                    </strong>

                    <p>
                      Developer registration
                      continue karne ke liye
                      one-time ₹{paymentAmount}{" "}
                      {paymentCurrency} payment
                      complete karein.
                    </p>

                    <button
                      type="button"
                      className="primary-button"
                      onClick={
                        handleOpenPayment
                      }
                    >
                      Pay ₹{paymentAmount}
                    </button>

                  </div>

                </div>
              )}

              {!paymentRequired &&
                developerActive && (
                  <div
                    className="alert alert-success"
                    style={{
                      marginTop: "20px",
                    }}
                  >

                    <div className="alert-icon">
                      ✓
                    </div>

                    <div>

                      <strong>
                        Developer account active
                      </strong>

                      <p>
                        Your developer account
                        is active. You can manage
                        and publish your apps.
                      </p>

                    </div>

                  </div>
                )}

              {!paymentRequired &&
                !developerActive && (
                  <div
                    className="alert alert-success"
                    style={{
                      marginTop: "20px",
                    }}
                  >

                    <div className="alert-icon">
                      ✓
                    </div>

                    <div>

                      <strong>
                        Payment status updated
                      </strong>

                      <p>
                        Payment requirement is
                        currently not active.
                        Developer verification
                        status is available
                        in your account.
                      </p>

                    </div>

                  </div>
                )}

            </div>

          )}

        </section>

        {/* =================================================
            DASHBOARD STATS
        ================================================= */}

        <section className="dashboard-stat-grid">

          <div className="dashboard-stat">

            <span className="dashboard-stat-label">
              Your Apps
            </span>

            <strong>
              {apps.length}
            </strong>

            <small>
              Total uploaded
            </small>

          </div>

          <div className="dashboard-stat">

            <span className="dashboard-stat-label">
              Downloads
            </span>

            <strong>
              {dashboardStats.downloads}
            </strong>

            <small>
              Total downloads
            </small>

          </div>

          <div className="dashboard-stat">

            <span className="dashboard-stat-label">
              Views
            </span>

            <strong>
              {dashboardStats.views}
            </strong>

            <small>
              Total app views
            </small>

          </div>

          <div className="dashboard-stat">

            <span className="dashboard-stat-label">
              Rating
            </span>

            <strong>
              {dashboardStats.averageRating.toFixed(
                1
              )}
            </strong>

            <small>
              Average rating
            </small>

          </div>

        </section>

        {/* =================================================
            GLOBAL MESSAGE
        ================================================= */}

        {error && (
          <div className="alert alert-error">

            <div className="alert-icon">
              !
            </div>

            <div>

              <strong>
                Something went wrong
              </strong>

              <p>
                {error}
              </p>

            </div>

          </div>
        )}

        {message && (
          <div className="alert alert-success">

            <div className="alert-icon">
              ✓
            </div>

            <div>

              <strong>
                Success
              </strong>

              <p>
                {message}
              </p>

            </div>

          </div>
        )}

        {/* =================================================
            DEVELOPER PROFILE
        ================================================= */}

        <section
          id="developer-profile"
          className="dashboard-section"
        >

          <div className="section-title section-title-row">

            <div>

              <span className="section-kicker">
                ACCOUNT
              </span>

              <h2>
                Developer profile
              </h2>

              <p>
                Manage your developer account
                information and verification status.
              </p>

            </div>

            {!profileLoading &&
              developerProfile &&
              !profileEditing && (

                <button
                  type="button"
                  className="refresh-button"
                  onClick={() => {
                    setProfileError("");
                    setProfileMessage("");
                    setProfileEditing(true);
                  }}
                >
                  Edit Profile
                </button>

              )}

          </div>

          {profileError && (
            <div className="alert alert-error">

              <div className="alert-icon">
                !
              </div>

              <div>

                <strong>
                  Profile error
                </strong>

                <p>
                  {profileError}
                </p>

              </div>

            </div>
          )}

          {profileMessage && (
            <div className="alert alert-success">

              <div className="alert-icon">
                ✓
              </div>

              <div>

                <strong>
                  Profile updated
                </strong>

                <p>
                  {profileMessage}
                </p>

              </div>

            </div>
          )}

          {profileLoading && (
            <div className="state-card professional-state">

              <div className="loading-spinner" />

              <div>

                <strong>
                  Loading developer profile
                </strong>

                <p>
                  Please wait while your account
                  information is loaded.
                </p>

              </div>

            </div>
          )}

          {!profileLoading &&
            developerProfile && (
              <div className="developer-profile-card">

                {!profileEditing ? (

                  <>
                    <div className="developer-profile-header">

                      <div className="developer-profile-avatar">
                        {developerProfile.full_name
                          ?.charAt(0)
                          ?.toUpperCase() || "D"}
                      </div>

                      <div className="developer-profile-heading">

                        <h3>
                          {developerProfile.full_name ||
                            "Developer"}
                        </h3>

                        <p>
                          {developerProfile.email}
                        </p>

                      </div>

                    </div>

                    <div className="developer-profile-status-grid">

                      <div className="profile-status-item">

                        <span>
                          Account
                        </span>

                        <strong>
                          {developerActive
                            ? "Developer Active"
                            : "Not Active"}
                        </strong>

                      </div>

                      <div className="profile-status-item">

                        <span>
                          Plan
                        </span>

                        <strong>
                          {developerPlan}
                        </strong>

                      </div>

                      <div className="profile-status-item">

                        <span>
                          Payment / Review
                        </span>

                        <strong>
                          {developerStatus}
                        </strong>

                      </div>

                      <div className="profile-status-item">

                        <span>
                          Developer Type
                        </span>

                        <strong>
                          {developerProfile.developer_type ||
                            "individual"}
                        </strong>

                      </div>

                    </div>

                    <div className="developer-profile-grid">

                      <div>
                        <span>
                          Country
                        </span>

                        <strong>
                          {developerProfile.country ||
                            "—"}
                        </strong>
                      </div>

                      <div>
                        <span>
                          Phone
                        </span>

                        <strong>
                          {developerProfile.phone ||
                            "—"}
                        </strong>
                      </div>

                      <div>
                        <span>
                          Company
                        </span>

                        <strong>
                          {developerProfile.company_name ||
                            "—"}
                        </strong>
                      </div>

                      <div>
                        <span>
                          Website
                        </span>

                        <strong>
                          {developerProfile.website ||
                            "—"}
                        </strong>
                      </div>

                      <div>
                        <span>
                          GitHub
                        </span>

                        <strong>
                          {developerProfile.github ||
                            "—"}
                        </strong>
                      </div>

                      <div>
                        <span>
                          Address
                        </span>

                        <strong>
                          {developerProfile.address ||
                            "—"}
                        </strong>
                      </div>

                    </div>

                    {developerProfile.bio && (
                      <div className="developer-profile-bio">

                        <span>
                          Bio
                        </span>

                        <p>
                          {developerProfile.bio}
                        </p>

                      </div>
                    )}

                  </>

                ) : (

                  <form
                    onSubmit={
                      handleProfileSave
                    }
                    className="professional-form profile-form"
                  >

                    <div className="form-section">

                      <div className="form-section-heading">

                        <span className="form-step">
                          01
                        </span>

                        <div>

                          <h3>
                            Basic information
                          </h3>

                          <p>
                            Update your public
                            developer information.
                          </p>

                        </div>

                      </div>

                      <div className="form-grid">

                        <div className="form-field">

                          <label htmlFor="profile-full-name">
                            Full Name
                          </label>

                          <input
                            id="profile-full-name"
                            name="full_name"
                            type="text"
                            value={
                              profileForm.full_name
                            }
                            onChange={
                              handleProfileChange
                            }
                            placeholder="Your full name"
                            required
                          />

                        </div>

                        <div className="form-field">

                          <label htmlFor="profile-developer-type">
                            Developer Type
                          </label>

                          <select
                            id="profile-developer-type"
                            name="developer_type"
                            value={
                              profileForm.developer_type
                            }
                            onChange={
                              handleProfileChange
                            }
                          >

                            <option value="individual">
                              Individual
                            </option>

                            <option value="organization">
                              Organization
                            </option>

                          </select>

                        </div>

                        <div className="form-field">

                          <label htmlFor="profile-country">
                            Country
                          </label>

                          <input
                            id="profile-country"
                            name="country"
                            type="text"
                            value={
                              profileForm.country
                            }
                            onChange={
                              handleProfileChange
                            }
                            placeholder="India"
                            required
                          />

                        </div>

                        <div className="form-field">

                          <label htmlFor="profile-phone">
                            Phone
                          </label>

                          <input
                            id="profile-phone"
                            name="phone"
                            type="tel"
                            value={
                              profileForm.phone
                            }
                            onChange={
                              handleProfileChange
                            }
                            placeholder="+91..."
                            required
                          />

                        </div>

                      </div>

                    </div>

                    <div className="form-section">

                      <div className="form-section-heading">

                        <span className="form-step">
                          02
                        </span>

                        <div>

                          <h3>
                            Professional information
                          </h3>

                          <p>
                            Add optional company,
                            website and profile details.
                          </p>

                        </div>

                      </div>

                      <div className="form-grid">

                        <div className="form-field">

                          <label htmlFor="profile-company">
                            Company Name
                          </label>

                          <input
                            id="profile-company"
                            name="company_name"
                            type="text"
                            value={
                              profileForm.company_name
                            }
                            onChange={
                              handleProfileChange
                            }
                            placeholder="Company or organization"
                          />

                        </div>

                        <div className="form-field">

                          <label htmlFor="profile-website">
                            Website
                          </label>

                          <input
                            id="profile-website"
                            name="website"
                            type="url"
                            value={
                              profileForm.website
                            }
                            onChange={
                              handleProfileChange
                            }
                            placeholder="https://example.com"
                          />

                        </div>

                        <div className="form-field">

                          <label htmlFor="profile-github">
                            GitHub
                          </label>

                          <input
                            id="profile-github"
                            name="github"
                            type="url"
                            value={
                              profileForm.github
                            }
                            onChange={
                              handleProfileChange
                            }
                            placeholder="https://github.com/username"
                          />

                        </div>

                      </div>

                    </div>

                    <div className="form-section">

                      <div className="form-section-heading">

                        <span className="form-step">
                          03
                        </span>

                        <div>

                          <h3>
                            Address and bio
                          </h3>

                          <p>
                            Provide additional information
                            about your developer account.
                          </p>

                        </div>

                      </div>

                      <div className="form-grid form-grid-single">

                        <div className="form-field">

                          <label htmlFor="profile-address">
                            Address
                          </label>

                          <textarea
                            id="profile-address"
                            name="address"
                            value={
                              profileForm.address
                            }
                            onChange={
                              handleProfileChange
                            }
                            rows={4}
                            placeholder="Your address"
                            required
                          />

                        </div>

                        <div className="form-field">

                          <label htmlFor="profile-bio">
                            Bio
                          </label>

                          <textarea
                            id="profile-bio"
                            name="bio"
                            value={
                              profileForm.bio
                            }
                            onChange={
                              handleProfileChange
                            }
                            rows={5}
                            placeholder="Tell users about yourself or your organization..."
                          />

                        </div>

                      </div>

                    </div>

                    <div className="form-submit-row">

                      <div className="submit-note">

                        <strong>
                          Save developer profile
                        </strong>

                        <span>
                          Your profile information
                          will be saved to your account.
                        </span>

                      </div>

                      <div className="profile-form-actions">

                        <button
                          type="button"
                          className="secondary-button"
                          onClick={
                            handleCancelProfileEdit
                          }
                          disabled={
                            profileSaving
                          }
                        >
                          Cancel
                        </button>

                        <button
                          type="submit"
                          className="primary-button"
                          disabled={
                            profileSaving
                          }
                        >
                          {profileSaving
                            ? "Saving..."
                            : "Save Profile"}
                        </button>

                      </div>

                    </div>

                  </form>

                )}

              </div>
            )}

        </section>

        {/* =================================================
            UPLOAD APP
        ================================================= */}

        {developerActive ? (

          <section
            id="upload-app"
            className="dashboard-section"
          >

            <div className="section-title">

              <div>

                <span className="section-kicker">
                  PUBLISH
                </span>

                <h2>
                  Upload a new app
                </h2>

                <p>
                  Add your Android application
                  to the PARAM Play Store marketplace.
                </p>

              </div>

            </div>

            <div className="upload-card">

              <form
                onSubmit={
                  handleUpload
                }
                className="professional-form"
              >

                <div className="form-section">

                  <div className="form-section-heading">

                    <span className="form-step">
                      01
                    </span>

                    <div>

                      <h3>
                        App information
                      </h3>

                      <p>
                        Basic information about
                        your application.
                      </p>

                    </div>

                  </div>

                  <div className="form-grid">

                    <div className="form-field">

                      <label htmlFor="app-name">
                        App Name
                      </label>

                      <input
                        id="app-name"
                        type="text"
                        value={appName}
                        onChange={(event) =>
                          setAppName(
                            event.target.value
                          )
                        }
                        placeholder="My Android App"
                        required
                      />

                    </div>

                    <div className="form-field">

                      <label htmlFor="package-name">
                        Package Name
                      </label>

                      <input
                        id="package-name"
                        type="text"
                        value={packageName}
                        onChange={(event) =>
                          setPackageName(
                            event.target.value
                          )
                        }
                        placeholder="com.example.myapp"
                        required
                      />

                      <small>
                        Example:
                        com.company.product
                      </small>

                    </div>

                    <div className="form-field">

                      <label htmlFor="version">
                        Version
                      </label>

                      <input
                        id="version"
                        type="text"
                        value={version}
                        onChange={(event) =>
                          setVersion(
                            event.target.value
                          )
                        }
                        placeholder="1.0.0"
                        required
                      />

                    </div>

                    <div className="form-field">

                      <label htmlFor="category">
                        Category
                      </label>

                      <select
                        id="category"
                        value={category}
                        onChange={(event) =>
                          setCategory(
                            event.target.value
                          )
                        }
                      >

                        {CATEGORIES.map(
                          (item) => (
                            <option
                              key={item}
                              value={item}
                            >
                              {item}
                            </option>
                          )
                        )}

                      </select>

                    </div>

                  </div>

                </div>

                <div className="form-section">

                  <div className="form-section-heading">

                    <span className="form-step">
                      02
                    </span>

                    <div>

                      <h3>
                        Store listing
                      </h3>

                      <p>
                        Help users understand
                        what your app does.
                      </p>

                    </div>

                  </div>

                  <div className="form-grid form-grid-single">

                    <div className="form-field">

                      <label htmlFor="description">
                        Description
                      </label>

                      <textarea
                        id="description"
                        value={description}
                        onChange={(event) =>
                          setDescription(
                            event.target.value
                          )
                        }
                        placeholder="App ke baare mein short description..."
                        rows={5}
                      />

                    </div>

                    <div className="form-field">

                      <label htmlFor="changelog">
                        Changelog
                      </label>

                      <textarea
                        id="changelog"
                        value={changelog}
                        onChange={(event) =>
                          setChangelog(
                            event.target.value
                          )
                        }
                        placeholder="What's new in this version..."
                        rows={4}
                      />

                    </div>

                  </div>

                </div>

                <div className="form-section">

                  <div className="form-section-heading">

                    <span className="form-step">
                      03
                    </span>

                    <div>

                      <h3>
                        App assets
                      </h3>

                      <p>
                        Upload your icon and
                        installable application.
                      </p>

                    </div>

                  </div>

                  <div className="file-grid">

                    <div className="file-upload-box">

                      <label
                        htmlFor="app-icon"
                        className="file-upload-label"
                      >

                        <span className="file-upload-icon">
                          +
                        </span>

                        <span>

                          <strong>
                            App Icon
                          </strong>

                          <small>
                            PNG, JPG, WEBP or SVG
                          </small>

                        </span>

                      </label>

                      <input
                        id="app-icon"
                        type="file"
                        accept=".png,.jpg,.jpeg,.webp,.svg"
                        onChange={
                          handleIconChange
                        }
                      />

                      {icon && (
                        <div className="selected-file">
                          ✓ {icon.name}
                        </div>
                      )}

                    </div>

                    <div className="file-upload-box featured-upload">

                      <label
                        htmlFor="app-file"
                        className="file-upload-label"
                      >

                        <span className="file-upload-icon">
                          ↑
                        </span>

                        <span>

                          <strong>
                            APK / AAB File
                          </strong>

                          <small>
                            Android package
                            up to server limit
                          </small>

                        </span>

                      </label>

                      <input
                        id="app-file"
                        type="file"
                        accept=".apk,.aab"
                        onChange={
                          handleFileChange
                        }
                        required
                      />

                      {file && (
                        <div className="selected-file">
                          ✓ {file.name}
                        </div>
                      )}

                    </div>

                  </div>

                </div>

                <div className="form-submit-row">

                  <div className="submit-note">

                    <strong>
                      Ready to publish?
                    </strong>

                    <span>
                      Check your app information
                      before uploading.
                    </span>

                  </div>

                  <button
                    type="submit"
                    className="primary-button"
                    disabled={loading}
                  >
                    {loading
                      ? "Uploading..."
                      : "Upload App"}
                  </button>

                </div>

              </form>

            </div>

          </section>

        ) : (

          <section
            id="upload-app"
            className="dashboard-section"
          >

            <div className="state-card">

              <span className="section-kicker">
                PUBLISHING LOCKED
              </span>

              <h2>
                Developer publishing is not active
              </h2>

              <p>
                App upload, update और publishing
                के लिए आपका developer account active
                होना जरूरी है।
              </p>

              {paymentRequired && (
                <button
                  type="button"
                  className="primary-button"
                  onClick={
                    handleOpenPayment
                  }
                >
                  Pay ₹{paymentAmount}
                </button>
              )}

            </div>

          </section>

        )}

        {/* =================================================
            YOUR APPS
        ================================================= */}

        <section
          id="your-apps"
          className="dashboard-section"
        >

          <div className="section-title section-title-row">

            <div>

              <span className="section-kicker">
                MANAGEMENT
              </span>

              <h2>
                Your apps
              </h2>

              <p>
                Manage versions, listings,
                files and app statistics.
              </p>

            </div>

            <button
              type="button"
              className="refresh-button"
              onClick={
                loadMyApps
              }
              disabled={
                appsLoading
              }
            >
              {appsLoading
                ? "Loading..."
                : "Refresh Apps"}
            </button>

          </div>

          {appsLoading && (
            <div className="state-card professional-state">

              <div className="loading-spinner" />

              <div>

                <strong>
                  Loading your apps
                </strong>

                <p>
                  Please wait while your
                  developer apps are loaded.
                </p>

              </div>

            </div>
          )}

          {!appsLoading &&
            !error &&
            apps.length === 0 && (
              <div className="empty-state">

                <div className="empty-state-icon">
                  +
                </div>

                <h3>
                  No apps yet
                </h3>

                <p>
                  Upload your first Android
                  application to get started.
                </p>

                {developerActive && (
                  <a
                    href="#upload-app"
                    className="primary-action"
                  >
                    Upload First App
                  </a>
                )}

              </div>
            )}

          {!appsLoading &&
            apps.length > 0 && (
              <div className="developer-app-grid">

                {apps.map((app) => (

                  <article
                    className="developer-app-card"
                    key={app.id}
                  >

                    <div className="developer-card-header">

                      <div className="developer-app-icon">

                        {app.icon_url ? (
                          <img
                            src={app.icon_url}
                            alt={`${app.app_name} icon`}
                          />
                        ) : (
                          app.app_name
                            ?.charAt(0)
                            ?.toUpperCase() ||
                          "A"
                        )}

                      </div>

                      <div className="developer-app-heading">

                        <div className="app-status-row">

                          <span className="status-badge">
                            {app.status ||
                              "published"}
                          </span>

                          <span className="category-badge">
                            {app.category ||
                              "Other"}
                          </span>

                        </div>

                        <h3>
                          {app.app_name}
                        </h3>

                        <p>
                          Version{" "}
                          {app.version}
                        </p>

                      </div>

                    </div>

                    {app.package_name && (
                      <div className="package-box">

                        <span>
                          Package
                        </span>

                        <strong>
                          {app.package_name}
                        </strong>

                      </div>
                    )}

                    {app.description?.trim() && (
                      <p className="developer-app-description">
                        {app.description}
                      </p>
                    )}

                    <div className="developer-meta-grid">

                      <div>

                        <span>
                          File
                        </span>

                        <strong>
                          {formatFileType(
                            app.file_type
                          )}
                        </strong>

                      </div>

                      <div>

                        <span>
                          Size
                        </span>

                        <strong>
                          {formatSize(
                            app.size_mb
                          )}
                        </strong>

                      </div>

                      <div>

                        <span>
                          Downloads
                        </span>

                        <strong>
                          {app.download_count ??
                            0}
                        </strong>

                      </div>

                      <div>

                        <span>
                          Views
                        </span>

                        <strong>
                          {app.view_count ??
                            0}
                        </strong>

                      </div>

                    </div>

                    <div className="rating-row">

                      <span className="rating-stars">
                        ★
                      </span>

                      <strong>
                        {Number(
                          app.rating ?? 0
                        ).toFixed(1)}
                      </strong>

                      <span>
                        ({app.review_count ??
                          0} reviews)
                      </span>

                    </div>

                    {app.changelog?.trim() && (
                      <div className="changelog-box">

                        <span>
                          Latest changelog
                        </span>

                        <p>
                          {app.changelog}
                        </p>

                      </div>
                    )}

                    <div className="developer-card-actions">

                      <button
                        type="button"
                        className="card-action secondary"
                        onClick={() =>
                          navigate(
                            `/apps/${app.id}`
                          )
                        }
                      >
                        View Details
                      </button>

                      <a
                        className="card-action primary"
                        href={getDownloadUrl(
                          app.id
                        )}
                      >
                        Download APK
                      </a>

                    </div>

                    <div className="developer-management-actions">

                      <button
                        type="button"
                        className="manage-button"
                        onClick={() =>
                          handleStartUpdate(
                            app
                          )
                        }
                        disabled={
                          !developerActive ||
                          updateLoading ||
                          deletingAppId ===
                            app.id
                        }
                      >
                        Edit / Update
                      </button>

                      <button
                        type="button"
                        className="manage-button danger"
                        onClick={() =>
                          handleDelete(
                            app
                          )
                        }
                        disabled={
                          !developerActive ||
                          deletingAppId ===
                            app.id
                        }
                      >
                        {deletingAppId ===
                        app.id
                          ? "Deleting..."
                          : "Delete"}
                      </button>

                    </div>

                    {/* =================================================
                        UPDATE FORM
                    ================================================= */}

                    {editingAppId ===
                      app.id && (

                      <form
                        onSubmit={(event) =>
                          handleUpdate(
                            event,
                            app.id
                          )
                        }
                        className="update-panel"
                      >

                        <div className="update-panel-header">

                          <div>

                            <span className="section-kicker">
                              EDIT APP
                            </span>

                            <h3>
                              Update application
                            </h3>

                          </div>

                          <button
                            type="button"
                            className="close-update-button"
                            onClick={
                              handleCancelUpdate
                            }
                            disabled={
                              updateLoading
                            }
                          >
                            ×
                          </button>

                        </div>

                        <div className="form-grid">

                          <div className="form-field">

                            <label>
                              Package Name
                            </label>

                            <input
                              type="text"
                              value={
                                updatePackageName
                              }
                              onChange={(
                                event
                              ) =>
                                setUpdatePackageName(
                                  event.target
                                    .value
                                )
                              }
                              placeholder="com.example.myapp"
                            />

                          </div>

                          <div className="form-field">

                            <label>
                              New Version
                            </label>

                            <input
                              type="text"
                              value={
                                updateVersion
                              }
                              onChange={(
                                event
                              ) =>
                                setUpdateVersion(
                                  event.target
                                    .value
                                )
                              }
                              placeholder="1.1.0"
                              required
                            />

                          </div>

                          <div className="form-field">

                            <label>
                              Category
                            </label>

                            <select
                              value={
                                updateCategory
                              }
                              onChange={(
                                event
                              ) =>
                                setUpdateCategory(
                                  event.target
                                    .value
                                )
                              }
                            >

                              {CATEGORIES.map(
                                (item) => (
                                  <option
                                    key={item}
                                    value={item}
                                  >
                                    {item}
                                  </option>
                                )
                              )}

                            </select>

                          </div>

                        </div>

                        <div className="form-field">

                          <label>
                            Description
                          </label>

                          <textarea
                            value={
                              updateDescription
                            }
                            onChange={(
                              event
                            ) =>
                              setUpdateDescription(
                                event.target
                                  .value
                              )
                            }
                            rows={4}
                            placeholder="App description..."
                          />

                        </div>

                        <div className="form-field">

                          <label>
                            Changelog
                          </label>

                          <textarea
                            value={
                              updateChangelog
                            }
                            onChange={(
                              event
                            ) =>
                              setUpdateChangelog(
                                event.target
                                  .value
                              )
                            }
                            rows={4}
                            placeholder="What's new..."
                          />

                        </div>

                        <div className="file-grid">

                          <div className="file-upload-box">

                            <label
                              htmlFor={`update-icon-${app.id}`}
                              className="file-upload-label"
                            >

                              <span className="file-upload-icon">
                                +
                              </span>

                              <span>

                                <strong>
                                  New App Icon
                                </strong>

                                <small>
                                  Optional
                                </small>

                              </span>

                            </label>

                            <input
                              id={`update-icon-${app.id}`}
                              type="file"
                              accept=".png,.jpg,.jpeg,.webp,.svg"
                              onChange={
                                handleUpdateIconChange
                              }
                            />

                            {updateIcon && (
                              <div className="selected-file">
                                ✓{" "}
                                {
                                  updateIcon.name
                                }
                              </div>
                            )}

                          </div>

                          <div className="file-upload-box featured-upload">

                            <label
                              htmlFor={`update-file-${app.id}`}
                              className="file-upload-label"
                            >

                              <span className="file-upload-icon">
                                ↑
                              </span>

                              <span>

                                <strong>
                                  New APK / AAB
                                </strong>

                                <small>
                                  Required for update
                                </small>

                              </span>

                            </label>

                            <input
                              id={`update-file-${app.id}`}
                              type="file"
                              accept=".apk,.aab"
                              onChange={
                                handleUpdateFileChange
                              }
                              required
                            />

                            {updateFile && (
                              <div className="selected-file">
                                ✓{" "}
                                {
                                  updateFile.name
                                }
                              </div>
                            )}

                          </div>

                        </div>

                        <div className="update-submit-row">

                          <button
                            type="submit"
                            className="primary-button"
                            disabled={
                              updateLoading
                            }
                          >
                            {updateLoading
                              ? "Updating..."
                              : "Save Update"}
                          </button>

                          <button
                            type="button"
                            className="secondary-button"
                            onClick={
                              handleCancelUpdate
                            }
                            disabled={
                              updateLoading
                            }
                          >
                            Cancel
                          </button>

                        </div>

                      </form>
                    )}

                  </article>

                ))}

              </div>
            )}

        </section>

      </main>

      {/* ===================================================
          FOOTER
      =================================================== */}

      <footer className="footer dashboard-footer">

        <span>

          <strong>
            PARAM Play Store
          </strong>{" "}
          Developer Marketplace

        </span>

        <span>
          Developer Dashboard
        </span>

      </footer>

    </div>
  );
}

export default Dashboard;