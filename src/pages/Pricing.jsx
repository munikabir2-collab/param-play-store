import { Link } from "react-router-dom";

function Pricing() {
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
        <h1>Pricing Details</h1>

        <p>
          NextStore displays the applicable price for each paid digital
          product on its product or application details page.
        </p>

        <h2>Product Pricing</h2>

        <p>
          Prices may vary depending on the individual product. The price
          displayed at the time of purchase is the applicable product price,
          subject to any clearly displayed taxes, offers or other applicable
          charges.
        </p>

        <h2>Payment</h2>

        <p>
          Customers may be offered available online payment methods through
          the payment gateway integrated with NextStore.
        </p>

        <h2>Price Changes</h2>

        <p>
          Product prices may be changed from time to time. Any change in
          price will apply to future purchases and will not change the price
          already confirmed for a completed transaction, except where
          required by law or due to an obvious pricing error.
        </p>

        <h2>Digital Products</h2>

        <p>
          Because the products offered through NextStore may be digital,
          access or delivery can occur electronically after a successful
          transaction, subject to the applicable product's terms.
        </p>

        <h2>Refunds</h2>

        <p>
          For information about eligible refunds, cancellations, failed
          transactions and duplicate payments, please see our Refund Policy.
        </p>

        <Link to="/refund-policy" className="legal-button">
          View Refund Policy
        </Link>
      </main>
    </div>
  );
}

export default Pricing;