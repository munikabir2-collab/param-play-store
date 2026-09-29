
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

      </Routes>
    </BrowserRouter>
  );
}


export default App;

