import { Link } from "react-router-dom";

function RefundPolicy() {
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
        <h1>Cancellation / Refund Policy</h1>

        <p>
          This policy explains how NextStore handles cancellation and refund
          requests for purchases made through the platform.
        </p>

        <h2>1. Failed Transactions</h2>

        <p>
          If a payment fails but the amount is temporarily debited from your
          bank account or payment method, the transaction may be processed or
          reversed by the payment gateway according to its applicable
          settlement and refund process.
        </p>

        <h2>2. Duplicate Payments</h2>

        <p>
          If you believe that you have been charged more than once for the
          same transaction, please contact support with the relevant
          transaction details so the payment can be reviewed.
        </p>

        <h2>3. Product Not Received</h2>

        <p>
          If payment has been successfully completed but the purchased
          digital product has not been delivered or made available, please
          contact support with your transaction information.
        </p>

        <h2>4. Defective or Non-Functional Product</h2>

        <p>
          If a purchased digital product does not function as described,
          please contact support and provide the product and transaction
          details. The issue will be reviewed based on the applicable product
          terms and circumstances.
        </p>

        <h2>5. Cancellation</h2>

        <p>
          Cancellation availability may depend on the nature and delivery
          status of the digital product. Once a digital product has been
          delivered or accessed, cancellation may be subject to the
          applicable product terms and applicable law.
        </p>

        <h2>6. Refund Review</h2>

        <p>
          Refund requests are reviewed individually based on the transaction,
          product, payment status and applicable terms. Where a refund is
          approved, it will normally be processed through the applicable
          payment method or payment gateway.
        </p>

        <h2>7. Refund Processing Time</h2>

        <p>
          After approval, the time required for the refunded amount to appear
          in the customer's account may depend on the payment provider and
          banking system.
        </p>

        <h2>8. Contact for Refunds</h2>

        <p>
          To request assistance regarding a cancellation or refund, please
          contact NextStore with your order or transaction details.
        </p>

        <Link to="/contact" className="legal-button">
          Contact Us for Support
        </Link>
      </main>
    </div>
  );
}

export default RefundPolicy;