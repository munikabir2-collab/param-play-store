import { Link } from "react-router-dom";

function Privacy() {
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
        <h1>Privacy Policy</h1>

        <p>
          This Privacy Policy explains how NextStore may collect, use and
          protect information when you use our website and services.
        </p>

        <h2>1. Information We May Collect</h2>

        <p>
          Depending on how you use the platform, information may include
          account information, contact information, order information,
          transaction-related information and technical information required
          to operate and secure the website.
        </p>

        <h2>2. How We Use Information</h2>

        <p>
          Information may be used to provide and maintain the service,
          process orders, provide product access, respond to support requests,
          prevent fraud and abuse, and improve the reliability and security of
          the platform.
        </p>

        <h2>3. Payment Information</h2>

        <p>
          Online payments may be processed through a third-party payment
          gateway. Payment credentials such as card or banking information
          may be handled by the applicable payment provider according to its
          policies and security practices.
        </p>

        <h2>4. Account Information</h2>

        <p>
          If you create an account, information associated with that account
          may be used to provide account functionality, authenticate users and
          manage purchases or product access.
        </p>

        <h2>5. Security</h2>

        <p>
          We take reasonable measures to protect information handled by the
          platform. However, no internet-based system can guarantee absolute
          security.
        </p>

        <h2>6. Third-Party Services</h2>

        <p>
          Certain services, such as payment processing or infrastructure
          services, may be provided by third parties. Their handling of
          information is subject to their applicable policies.
        </p>

        <h2>7. Data Retention</h2>

        <p>
          Information may be retained for as long as reasonably necessary for
          providing services, maintaining transaction records, complying with
          legal obligations and resolving disputes.
        </p>

        <h2>8. Policy Updates</h2>

        <p>
          This Privacy Policy may be updated periodically. Any updated version
          will be published on this page.
        </p>

        <h2>9. Contact</h2>

        <p>
          If you have questions about this Privacy Policy or your information,
          please contact NextStore through the Contact Us page.
        </p>

        <Link to="/contact" className="legal-button">
          Contact Us
        </Link>
      </main>
    </div>
  );
}

export default Privacy;