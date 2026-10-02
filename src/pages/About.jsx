import { Link } from "react-router-dom";

function About() {
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
        <h1>About Us</h1>

        <p>
          Welcome to NextStore, an online platform for discovering and
          accessing digital applications and software products.
        </p>

        <p>
          NextStore provides users with information about available digital
          products and, where applicable, allows users to purchase and access
          eligible products through the platform.
        </p>

        <h2>Our Platform</h2>

        <p>
          Our goal is to provide a simple and convenient digital marketplace
          where users can explore applications, review product information,
          and access products available on the platform.
        </p>

        <h2>Digital Products</h2>

        <p>
          Products listed on NextStore may include software applications and
          other digital products. Product descriptions, availability and
          applicable prices are displayed on the relevant product pages.
        </p>

        <h2>Payments</h2>

        <p>
          Where online payment is available, payments are processed through
          supported payment gateway services. Payment-related information is
          handled according to the applicable payment provider's policies.
        </p>

        <h2>Contact</h2>

        <p>
          If you have questions about NextStore, products, payments or
          orders, please visit our Contact Us page.
        </p>

        <Link to="/contact" className="legal-button">
          Contact Us
        </Link>
      </main>
    </div>
  );
}

export default About;