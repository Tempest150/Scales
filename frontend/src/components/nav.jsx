import { useState } from "react";
import { Link, useLocation } from "react-router";
import {  BarChart, BoxArrowRight } from "react-bootstrap-icons";

const navLinks = [
  {
    href: "/dashboard",
    label: "Dashboard",
    icon: <BarChart className="me-2" />,
  },
];

export default function Navbar({ user, onLogout }) {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();

  return (
    <nav
      className="navbar navbar-expand-md navbar-dark bg-primary"
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="container position-relative">
        <span className="navbar-brand fw-semibold">Leo</span>

        <button
          className="navbar-toggler"
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          aria-controls="mobile-menu"
          aria-expanded={isOpen}
          aria-label={isOpen ? "Close menu" : "Open menu"}
        >
          <span className="navbar-toggler-icon" />
        </button>

        <div
          className={`collapse navbar-collapse ${isOpen ? "show" : ""}`}
          id="mobile-menu"
        >
          <ul className="navbar-nav ms-auto gap-1 align-items-md-center">
            {navLinks.map((link) => (
              <li key={link.href}>
                <Link
                  to={link.href}
                  className="nav-link"
                  onClick={() => setIsOpen(false)}
                  aria-current={
                    location.pathname === link.href ? "page" : undefined
                  }
                >
                  {link.icon}
                  {link.label}
                </Link>
              </li>
            ))}

            {user && (
              <li className="nav-item ms-md-2 d-flex align-items-center gap-2">
                <span className="text-white-50" style={{ fontSize: 13 }}>
                  {user.name || user.email}
                </span>
                <button
                  onClick={onLogout}
                  className="btn btn-sm btn-outline-light d-flex align-items-center gap-1"
                  style={{ fontSize: 13 }}
                  title="Sign out"
                >
                  <BoxArrowRight /> Sign out
                </button>
              </li>
            )}
          </ul>
        </div>
      </div>
    </nav>
  );
}
