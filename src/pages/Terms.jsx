import { Link } from "react-router-dom";

function Terms() {
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
        <h1>Terms & Conditions</h1>

        <p>
          By accessing or using NextStore, you agree to comply with these
          Terms & Conditions. If you do not agree with these terms, please do
          not use the platform.
        </p>

        <h2>1. Use of the Platform</h2>

        <p>
          You agree to use NextStore only for lawful purposes and in a manner
          that does not interfere with the operation, security or availability
          of the platform.
        </p>

        <h2>2. User Accounts</h2>

        <p>
          Where an account is required, users are responsible for providing
          accurate information and maintaining the security of their account
          credentials.
        </p>

        <h2>3. Products</h2>

        <p>
          Product information, descriptions, pricing and availability are
          provided on the relevant product pages. Digital products may be
          subject to additional product-specific conditions.
        </p>

        <h2>4. Payments</h2>

        <p>
          Payments for eligible products may be processed through an
          authorized payment gateway. A transaction may be subject to the
          payment gateway's own terms and policies.
        </p>

        <h2>5. Digital Product Access</h2>

        <p>
          Access or delivery of a digital product may depend on successful
          payment and the applicable product's delivery mechanism.
        </p>

        <h2>6. Intellectual Property</h2>

        <p>
          Content, software, branding, text, graphics and other materials on
          NextStore may be protected by applicable intellectual-property
          laws. Users must not copy, redistribute or misuse such materials
          without appropriate authorization.
        </p>

        <h2>7. Prohibited Activities</h2>

        <p>
          Users must not use NextStore for unlawful activity, fraud,
          unauthorized access, abuse of payment systems, distribution of
          malicious software or activities that may harm the platform or
          other users.
        </p>

        <h2>8. Service Availability</h2>

        <p>
          We may temporarily suspend or modify parts of the platform for
          maintenance, security, upgrades or other operational reasons.
        </p>

        <h2>9. Changes to These Terms</h2>

        <p>
          These Terms & Conditions may be updated when necessary. Updated
          terms will be published on this page.
        </p>

        <h2>10. Contact</h2>

        <p>
          For questions regarding these terms, please visit our Contact Us
          page.
        </p>

        <Link to="/contact" className="legal-button">
          Contact Us
        </Link>
      </main>
    </div>
  );
}

export default Terms;