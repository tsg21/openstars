import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import App from "./App";

describe("App", () => {
  it("renders the layout shell", () => {
    render(<App />);
    // Title appears in both the desktop gate and top bar
    const titles = screen.getAllByText("OpenStars!");
    expect(titles.length).toBeGreaterThanOrEqual(1);
  });

  it("renders the galaxy map canvas", () => {
    render(<App />);
    const canvas = document.querySelector("canvas");
    expect(canvas).toBeInTheDocument();
  });

  it("renders the event log", () => {
    render(<App />);
    expect(screen.getByText("Events")).toBeInTheDocument();
  });

  it("renders the detail panel", () => {
    render(<App />);
    expect(screen.getByText("Nothing selected")).toBeInTheDocument();
  });
});
