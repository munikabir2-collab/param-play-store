import { Link } from "react-router-dom";

function Contact() {
  return (
    <div className="legal-page">
      <header className="legal-header">
        <Link to="/" className="brand">
          NextStore
        </Link>

        <nav>
          <Link to="/about">About Us</Link>
          <Link to="/pricing">Pricing</Link>
          <Link to="/contact">Contact Us</Link>
          <Link to="/terms">Terms</Link>
          <Link to="/privacy">Privacy</Link>
          <Link to="/refund-policy">Refund Policy</Link>
        </nav>
      </header>

      <main className="legal-container">
        <h1>Contact Us</h1>

        <p>
          We are available to assist with questions related to products,
          orders, payments, account access and other NextStore services.
        </p>

        <h2>Customer Support</h2>

        <p>
          For support, please use the customer-support contact information
          provided on the NextStore platform or in your order/account
          communication.
        </p>

        <h2>Payment Issues</h2>

        <p>
          If money has been deducted but your order or product access has not
          been completed, please contact us with the transaction details so
          that the payment can be reviewed.
        </p>

        <h2>Product Support</h2>

        <p>
          For an issue with a digital product, please provide the relevant
          product name and order or transaction information when contacting
          support.
        </p>

        <div className="contact-notice">
          <strong>Important:</strong> Before submitting the website for
          payment-gateway verification, replace this section with your actual
          public customer-support email address and/or phone number.
        </div>

        <h2>Website</h2>

        <p>
          NextStore website:
        </p>

        <a
          href="https://param-play-store.onrender.com"
          target="_blank"
          rel="noopener noreferrer"
        >
          https://param-play-store.onrender.com
        </a>

        <br />
        <br />

        <Link to="/" className="legal-button">
          Back to NextStore
        </Link>
      </main>
    </div>
  );
}

export default Contact;