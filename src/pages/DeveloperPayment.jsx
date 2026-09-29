
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  getDeveloperPaymentStatus,
  createDeveloperPaymentOrder,
  verifyDeveloperPayment,
} from "../api/client";

const RAZORPAY_SCRIPT_URL =
  "https://checkout.razorpay.com/v1/checkout.js";

const RAZORPAY_KEY_ID =
  import.meta.env.VITE_RAZORPAY_KEY_ID || "";

function loadRazorpayScript() {
  return new Promise((resolve) => {
    const existingScript = document.querySelector(
      `script[src="${RAZORPAY_SCRIPT_URL}"]`
    );

    if (existingScript) {
      if (window.Razorpay) {
        resolve(true);
      } else {
        existingScript.addEventListener(
          "load",
          () => resolve(true),
          { once: true }
        );

        existingScript.addEventListener(
          "error",
          () => resolve(false),
          { once: true }
        );
      }

      return;
    }

    const script = document.createElement("script");

    script.src = RAZORPAY_SCRIPT_URL;
    script.async = true;

    script.onload = () => {
      resolve(true);
    };

    script.onerror = () => {
      resolve(false);
    };

    document.body.appendChild(script);
  });
}

function getErrorMessage(error) {
  return (
    error?.response?.data?.detail ||
    error?.response?.data?.message ||
    error?.message ||
    "Something went wrong. Please try again."
  );
}

function DeveloperPayment() {
  const navigate = useNavigate();

  const [paymentStatus, setPaymentStatus] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [creatingOrder, setCreatingOrder] =
    useState(false);

  const [message, setMessage] =
    useState("");

  const [error, setError] =
    useState("");

  const token =
    localStorage.getItem("PARAM Play Store_token");

  // =====================================================
  // LOAD PAYMENT STATUS
  // =====================================================

  const loadPaymentStatus = async () => {
    const currentToken =
      localStorage.getItem("PARAM Play Store_token");

    if (!currentToken) {
      navigate("/login");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const data =
        await getDeveloperPaymentStatus(
          currentToken
        );

      setPaymentStatus(data);

    } catch (err) {
      console.error(
        "Developer payment status error:",
        err
      );

      const status =
        err?.response?.status;

      if (status === 401) {
        localStorage.removeItem(
          "PARAM Play Store_token"
        );

        navigate("/login");
        return;
      }

      if (
        status === 403 ||
        status === 404
      ) {
        setPaymentStatus(null);

        setError(
          "Developer payment is available only for users who have a developer application."
        );

        return;
      }

      setError(
        getErrorMessage(err)
      );

    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPaymentStatus();
  }, []);

  // =====================================================
  // START RAZORPAY PAYMENT
  // =====================================================

  const handlePayment = async () => {
    const currentToken =
      localStorage.getItem("PARAM Play Store_token");

    if (!currentToken) {
      navigate("/login");
      return;
    }

    if (!RAZORPAY_KEY_ID) {
      setError(
        "Razorpay public Key ID is not configured in the frontend."
      );
      return;
    }

    try {
      setCreatingOrder(true);
      setError("");
      setMessage("");

      // -------------------------------------------------
      // LOAD RAZORPAY CHECKOUT
      // -------------------------------------------------

      const razorpayLoaded =
        await loadRazorpayScript();

      if (!razorpayLoaded) {
        throw new Error(
          "Razorpay Checkout could not be loaded. Please check your internet connection."
        );
      }

      if (
        typeof window.Razorpay !==
        "function"
      ) {
        throw new Error(
          "Razorpay Checkout is not available."
        );
      }

      // -------------------------------------------------
      // CREATE PAYMENT ORDER
      // -------------------------------------------------

      const order =
        await createDeveloperPaymentOrder(
          currentToken,
          "INR"
        );

      if (!order?.order_id) {
        throw new Error(
          "Backend did not return a valid Razorpay order ID."
        );
      }

      // -------------------------------------------------
      // AMOUNT
      // -------------------------------------------------

      const amountInRupees =
        Number(order.amount || 999);

      const amountInPaise =
        Math.round(
          amountInRupees * 100
        );

      // -------------------------------------------------
      // RAZORPAY OPTIONS
      // -------------------------------------------------

      const options = {
        key: RAZORPAY_KEY_ID,

        amount:
          amountInPaise,

        currency:
          order.currency ||
          "INR",

        name:
          "PARAM Play Store",

        description:
          "Developer Registration Fee",

        order_id:
          order.order_id,

        handler:
          async function (response) {
            try {
              setCreatingOrder(true);
              setError("");
              setMessage(
                "Payment received. Verifying payment..."
              );

              const orderId =
                response?.razorpay_order_id;

              const paymentId =
                response?.razorpay_payment_id;

              const signature =
                response?.razorpay_signature;

              if (
                !orderId ||
                !paymentId ||
                !signature
              ) {
                throw new Error(
                  "Razorpay did not return complete payment verification details."
                );
              }

              // ------------------------------------------------
              // VERIFY PAYMENT WITH BACKEND
              // ------------------------------------------------

              const verification =
                await verifyDeveloperPayment(
                  orderId,
                  paymentId,
                  signature,
                  currentToken
                );

              if (
                verification?.success
              ) {
                setMessage(
                  verification.message ||
                    "Payment verified successfully."
                );

                await loadPaymentStatus();

              } else {
                setError(
                  verification?.message ||
                    "Payment verification failed."
                );
              }

            } catch (err) {
              console.error(
                "Payment verification error:",
                err
              );

              setError(
                getErrorMessage(err)
              );

            } finally {
              setCreatingOrder(false);
            }
          },

        modal: {
          ondismiss: function () {
            setCreatingOrder(false);

            setMessage(
              "Payment window closed."
            );
          },
        },

        prefill: {
          email: "",
          name: "",
          contact: "",
        },

        notes: {
          payment_type:
            "developer_registration",
        },

        theme: {
          color: "#172033",
        },

        retry: {
          enabled: true,
        },
      };

      // -------------------------------------------------
      // OPEN RAZORPAY
      // -------------------------------------------------

      const razorpay =
        new window.Razorpay(
          options
        );

      // -------------------------------------------------
      // PAYMENT FAILED
      // -------------------------------------------------

      razorpay.on(
        "payment.failed",
        function (response) {
          console.error(
            "Razorpay payment failed:",
            response
          );

          setCreatingOrder(false);

          setError(
            response?.error?.description ||
              "Payment failed. Please try again."
          );
        }
      );

      razorpay.open();

    } catch (err) {
      console.error(
        "Payment start error:",
        err
      );

      const status =
        err?.response?.status;

      if (status === 401) {
        localStorage.removeItem(
          "PARAM Play Store_token"
        );

        navigate("/login");
        return;
      }

      if (status === 400) {
        const detail =
          err?.response?.data?.detail ||
          "";

        if (
          detail
            .toLowerCase()
            .includes("already active")
        ) {
          setMessage(
            "Your developer account is already active."
          );

          await loadPaymentStatus();

          return;
        }
      }

      setError(
        getErrorMessage(err)
      );

      setCreatingOrder(false);
    }
  };

  // =====================================================
  // LOADING
  // =====================================================

  if (loading) {
    return (
      <div className="page">
        <div className="container">

          <div className="state-card">

            <h2>
              Loading payment status...
            </h2>

            <p>
              Please wait while we check
              your developer account.
            </p>

          </div>

        </div>
      </div>
    );
  }

  // =====================================================
  // NOT A DEVELOPER / STATUS ERROR
  // =====================================================

  if (
    error &&
    !paymentStatus
  ) {
    return (
      <div className="page">

        <div className="container">

          <div className="error-card">

            <h2>
              Developer Payment
            </h2>

            <p>
              {error}
            </p>

            <div
              style={{
                display: "flex",
                gap: "10px",
                flexWrap: "wrap",
                marginTop: "20px",
              }}
            >

              <button
                className="retry-button"
                onClick={
                  loadPaymentStatus
                }
              >
                Retry
              </button>

              <button
                className="refresh-button"
                onClick={() =>
                  navigate("/profile")
                }
              >
                Go to Profile
              </button>

            </div>

          </div>

        </div>

      </div>
    );
  }

  // =====================================================
  // BACKEND PAYMENT STATUS
  // =====================================================

  const paymentRequired =
    Boolean(
      paymentStatus?.payment_required
    );

  const currentStatus =
    paymentStatus?.payment_status ||
    "unknown";

  const paymentType =
    paymentStatus?.payment_type ||
    "developer_registration";

  const amount =
    paymentStatus?.amount ||
    "999.00";

  const currency =
    paymentStatus?.currency ||
    "INR";

  const isPaid =
    currentStatus === "paid";

  // =====================================================
  // PAYMENT NOT REQUIRED
  // =====================================================

  if (!paymentRequired) {
    return (
      <div className="page">

        <div className="container">

          <div className="hero">

            <div>

              <p className="eyebrow">
                DEVELOPER ACCOUNT
              </p>

              <h1>
                Developer account is active
              </h1>

              <p className="hero-text">
                Your account does not currently
                require a developer registration
                payment.
              </p>

            </div>

            <div className="hero-stat">

              <strong>
                âœ“
              </strong>

              <span>
                Active
              </span>

            </div>

          </div>

          <div className="state-card">

            <h2>
              Payment Status
            </h2>

            <p>
              Status:{" "}
              <strong>
                {currentStatus}
              </strong>
            </p>

            <p>
              Payment Type:{" "}
              <strong>
                {paymentType}
              </strong>
            </p>

            <p>
              Amount:{" "}
              <strong>
                â‚¹{amount}
              </strong>
            </p>

            <p>
              Currency:{" "}
              <strong>
                {currency}
              </strong>
            </p>

            <button
              className="retry-button"
              onClick={() =>
                navigate("/dashboard")
              }
            >
              Go to Dashboard
            </button>

          </div>

        </div>

      </div>
    );
  }

  // =====================================================
  // PAYMENT ALREADY PAID
  // =====================================================

  if (isPaid) {
    return (
      <div className="page">

        <div className="container">

          <div className="hero">

            <div>

              <p className="eyebrow">
                PAYMENT RECEIVED
              </p>

              <h1>
                Payment verified
              </h1>

              <p className="hero-text">
                Your developer registration
                payment has been successfully
                processed.
              </p>

            </div>

            <div className="hero-stat">

              <strong>
                âœ“
              </strong>

              <span>
                Paid
              </span>

            </div>

          </div>

          <div className="state-card">

            <h2>
              Payment Details
            </h2>

            <p>
              Status:{" "}
              <strong>
                Paid
              </strong>
            </p>

            <p>
              Payment Type:{" "}
              <strong>
                {paymentType}
              </strong>
            </p>

            <p>
              Amount:{" "}
              <strong>
                â‚¹{amount}
              </strong>
            </p>

            <p>
              Currency:{" "}
              <strong>
                {currency}
              </strong>
            </p>

            <div
              style={{
                marginTop: "20px",
                padding: "14px",
                borderRadius: "9px",
                background: "#eef7ee",
                color: "#285c32",
              }}
            >
              Payment successful. Your
              developer account will become
              active after the required
              verification is approved.
            </div>

            <button
              className="retry-button"
              style={{
                marginTop: "20px",
              }}
              onClick={() =>
                navigate("/dashboard")
              }
            >
              Go to Dashboard
            </button>

          </div>

        </div>

      </div>
    );
  }

  // =====================================================
  // PAYMENT REQUIRED
  // =====================================================

  return (
    <div className="page">

      <div className="container">

        {/* =================================================
            HERO
        ================================================== */}

        <div className="hero">

          <div>

            <p className="eyebrow">
              PARAM Play Store DEVELOPER
            </p>

            <h1>
              Complete your developer
              registration
            </h1>

            <p className="hero-text">
              Pay the one-time developer
              registration fee to continue
              your developer verification
              process.
            </p>

          </div>

          <div className="hero-stat">

            <strong>
              â‚¹{amount}
            </strong>

            <span>
              One-time fee
            </span>

          </div>

        </div>

        {/* =================================================
            PAYMENT CARD
        ================================================== */}

        <div className="state-card">

          <h2>
            Developer Registration Payment
          </h2>

          <p>
            Payment type:{" "}
            <strong>
              {paymentType}
            </strong>
          </p>

          <p>
            Amount:{" "}
            <strong>
              â‚¹{amount}
            </strong>
          </p>

          <p>
            Currency:{" "}
            <strong>
              {currency}
            </strong>
          </p>

          {message && (
            <div
              style={{
                marginTop: "20px",
                padding: "14px",
                borderRadius: "9px",
                background: "#eef7ee",
                color: "#285c32",
              }}
            >
              {message}
            </div>
          )}

          {error && (
            <div
              style={{
                marginTop: "20px",
                padding: "14px",
                borderRadius: "9px",
                background: "#fff0f0",
                color: "#8a2f2f",
              }}
            >
              {error}
            </div>
          )}

          <button
            className="download-button"
            style={{
              border: "none",
              cursor:
                creatingOrder
                  ? "wait"
                  : "pointer",
              marginTop: "24px",
              opacity:
                creatingOrder
                  ? 0.7
                  : 1,
            }}
            onClick={
              handlePayment
            }
            disabled={
              creatingOrder
            }
          >
            {creatingOrder
              ? "Processing..."
              : `Pay â‚¹${amount}`}
          </button>

          <button
            className="refresh-button"
            style={{
              width: "100%",
              marginTop: "12px",
            }}
            onClick={() =>
              navigate("/dashboard")
            }
          >
            Back to Dashboard
          </button>

        </div>

        {/* =================================================
            PAYMENT PROCESS
        ================================================== */}

        <div className="state-card">

          <h2>
            What happens after payment?
          </h2>

          <p>
            <strong>1.</strong>{" "}
            Razorpay securely processes
            your payment.
          </p>

          <p>
            <strong>2.</strong>{" "}
            PARAM Play Store verifies the payment
            with the backend.
          </p>

          <p>
            <strong>3.</strong>{" "}
            Your developer application
            continues through verification.
          </p>

          <p>
            <strong>4.</strong>{" "}
            After the required verification
            is approved, your developer account
            becomes active.
          </p>

        </div>

        {/* =================================================
            SECURITY INFORMATION
        ================================================== */}

        <div className="state-card">

          <h2>
            Secure Payment
          </h2>

          <p>
            Your Razorpay secret key is never
            exposed in this frontend application.
          </p>

          <p>
            Only the public Razorpay Key ID is
            used by Checkout.
          </p>

          <p>
            Final payment verification is
            performed by the PARAM Play Store backend.
          </p>

        </div>

      </div>

    </div>
  );
}

export default DeveloperPayment;


