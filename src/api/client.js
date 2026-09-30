
import axios from "axios";

const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    Accept: "application/json",
  },
});

// =======================================================
// SIGNUP
// =======================================================

export const signupUser = async (userData) => {
  const response = await api.post(
    "/auth/signup",
    userData
  );

  return response.data;
};

// =======================================================
// LOGIN
// =======================================================

export const loginUser = async (
  email,
  password
) => {
  const formData = new URLSearchParams();

  formData.append("username", email);
  formData.append("password", password);

  const response = await api.post(
    "/auth/login",
    formData,
    {
      headers: {
        "Content-Type":
          "application/x-www-form-urlencoded",
      },
    }
  );

  return response.data;
};

// =======================================================
// CURRENT USER
// =======================================================

export const getCurrentUser = async (
  token
) => {
  const response = await api.get(
    "/auth/me",
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data;
};

// =======================================================
// PUBLIC APPS
// =======================================================

export const getApps = async () => {
  const response = await api.get("/apps/");
  return response.data;
};

// =======================================================
// APP DETAILS
// =======================================================

export const getAppDetails = async (
  appId
) => {
  const response = await api.get(
    `/apps/${appId}`
  );

  return response.data;
};

// =======================================================
// DEVELOPER APPLICATION
// =======================================================

export const applyDeveloper = async (
  application,
  token
) => {
  const response = await api.post(
    "/developers/apply",
    application,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data;
};

// =======================================================
// DEVELOPER PROFILE / APPLICATION
// =======================================================

export const getDeveloperMe = async (
  token
) => {
  const response = await api.get(
    "/developers/me",
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data;
};

// =======================================================
// DEVELOPER ACCOUNT
// =======================================================

export const getMyDeveloperProfile =
  async (token) => {
    const response = await api.get(
      "/developers/me/account",
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    return response.data;
  };

// =======================================================
// UPDATE DEVELOPER ACCOUNT
// =======================================================

export const updateMyDeveloperProfile =
  async (
    profileData,
    token
  ) => {
    const response = await api.put(
      "/developers/me/account",
      profileData,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      }
    );

    return response.data;
  };

// =======================================================
// DEVELOPER VERIFICATION STATUS
// =======================================================

export const getDeveloperVerificationStatus =
  async (token) => {
    const response = await api.get(
      "/developers/verification-status",
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    return response.data;
  };

// =======================================================
// DEVELOPER PAYMENT STATUS
// =======================================================

export const getDeveloperPaymentStatus =
  async (token) => {
    const response = await api.get(
      "/payments/developer/status",
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    return response.data;
  };

// =======================================================
// CREATE DEVELOPER PAYMENT ORDER
// =======================================================

export const createDeveloperPaymentOrder =
  async (
    token,
    currency = "INR"
  ) => {
    const response = await api.post(
      "/payments/developer/create-order",
      {
        currency,
      },
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      }
    );

    return response.data;
  };

// =======================================================
// VERIFY DEVELOPER PAYMENT
// =======================================================

export const verifyDeveloperPayment =
  async (
    orderId,
    paymentId,
    signature,
    token
  ) => {
    const response = await api.post(
      "/payments/developer/verify",
      {
        order_id: orderId,
        payment_id: paymentId,
        signature,
      },
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      }
    );

    return response.data;
  };

// =======================================================
// UPLOAD APP
// =======================================================

export const uploadApp = async (
  appName,
  packageName,
  version,
  file,
  token,
  description = "",
  category = "Other",
  changelog = "",
  icon = null
) => {
  const formData = new FormData();

  formData.append(
    "app_name",
    appName
  );

  formData.append(
    "package_name",
    packageName || ""
  );

  formData.append(
    "version",
    version
  );

  formData.append(
    "description",
    description || ""
  );

  formData.append(
    "category",
    category || "Other"
  );

  formData.append(
    "changelog",
    changelog || ""
  );

  formData.append(
    "file",
    file
  );

  if (icon) {
    formData.append(
      "icon",
      icon
    );
  }

  const response = await api.post(
    "/apps/upload",
    formData,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data;
};

// =======================================================
// MY APPS
// =======================================================

export const getMyApps = async (
  token
) => {
  const response = await api.get(
    "/apps/mine",
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data;
};

// =======================================================
// DOWNLOAD URL
// =======================================================

export const getDownloadUrl = (
  appId
) => {
  return `${API_URL}/apps/${appId}/download`;
};

// =======================================================
// UPDATE APP
// =======================================================

export const updateApp = async (
  appId,
  version,
  file,
  token,
  packageName = null,
  description = null,
  category = null,
  changelog = null,
  icon = null
) => {
  const formData = new FormData();

  formData.append(
    "version",
    version
  );

  if (packageName !== null) {
    formData.append(
      "package_name",
      packageName || ""
    );
  }

  if (description !== null) {
    formData.append(
      "description",
      description || ""
    );
  }

  if (category !== null) {
    formData.append(
      "category",
      category || "Other"
    );
  }

  if (changelog !== null) {
    formData.append(
      "changelog",
      changelog || ""
    );
  }

  formData.append(
    "file",
    file
  );

  if (icon) {
    formData.append(
      "icon",
      icon
    );
  }

  const response = await api.put(
    `/apps/${appId}/update`,
    formData,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data;
};

// =======================================================
// DELETE APP
// =======================================================

export const deleteApp = async (
  appId,
  token
) => {
  const response = await api.delete(
    `/apps/${appId}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data;
};

