import {
  BrowserRouter,
  Routes,
  Route,
} from "react-router-dom";

import Home from "./pages/Home";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import AppDetails from "./pages/AppDetails";
import Profile from "./pages/Profile";
import DeveloperPayment from "./pages/DeveloperPayment";

import About from "./pages/About";
import Pricing from "./pages/Pricing";
import Contact from "./pages/Contact";
import Terms from "./pages/Terms";
import Privacy from "./pages/Privacy";
import RefundPolicy from "./pages/RefundPolicy";

import "./index.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>

        <Route
          path="/"
          element={<Home />}
        />

        <Route
          path="/login"
          element={<Login />}
        />

        <Route
          path="/signup"
          element={<Signup />}
        />

        <Route
          path="/profile"
          element={<Profile />}
        />

        <Route
          path="/dashboard"
          element={<Dashboard />}
        />

        <Route
          path="/developer/payment"
          element={<DeveloperPayment />}
        />

        <Route
          path="/apps/:appId"
          element={<AppDetails />}
        />

        <Route
          path="/about"
          element={<About />}
        />

        <Route
          path="/pricing"
          element={<Pricing />}
        />

        <Route
          path="/contact"
          element={<Contact />}
        />

        <Route
          path="/terms"
          element={<Terms />}
        />

        <Route
          path="/privacy"
          element={<Privacy />}
        />

        <Route
          path="/refund-policy"
          element={<RefundPolicy />}
        />

      </Routes>
    </BrowserRouter>
  );
}

export default App;