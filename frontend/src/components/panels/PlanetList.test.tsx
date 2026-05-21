import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { PlanetList } from "./PlanetList";
import type { PlanetListColumn, PlanetListFilter } from "./PlanetList";
import type { PlayerPlanet } from "../../types";

function makePlanet(id: string, name: string): PlayerPlanet {
  return {
    id,
    name,
    x: 0,
    y: 0,
    scanLevel: "detailed",
    scanAge: 0,
    owner: "tim",
  };
}

const nameCol: PlanetListColumn = {
  id: "name",
  header: "Name",
  sortable: true,
  sortValue: (p) => p.name,
  render: (p) => p.name,
};

const noSortCol: PlanetListColumn = {
  id: "fixed",
  header: "Fixed",
  sortable: false,
  render: (p) => p.id,
};

const planets = [makePlanet("p1", "Zeta"), makePlanet("p2", "Alpha"), makePlanet("p3", "Mars")];

describe("PlanetList", () => {
  it("renders one row per planet in default name-sorted order", () => {
    render(
      <PlanetList
        planets={planets}
        selectedPlanetId={null}
        onSelectPlanet={() => undefined}
        columns={[nameCol]}
      />,
    );
    const rows = screen.getAllByRole("row").slice(1); // skip header
    expect(rows[0]).toHaveTextContent("Alpha");
    expect(rows[1]).toHaveTextContent("Mars");
    expect(rows[2]).toHaveTextContent("Zeta");
  });

  it("calls onSelectPlanet with the row id when a row is clicked", () => {
    const onSelect = vi.fn();
    render(
      <PlanetList
        planets={planets}
        selectedPlanetId={null}
        onSelectPlanet={onSelect}
        columns={[nameCol]}
      />,
    );
    fireEvent.click(screen.getByText("Mars"));
    expect(onSelect).toHaveBeenCalledWith("p3");
  });

  it("marks the selected row with aria-selected and accent class", () => {
    render(
      <PlanetList
        planets={planets}
        selectedPlanetId="p2"
        onSelectPlanet={() => undefined}
        columns={[nameCol]}
      />,
    );
    const rows = screen.getAllByRole("row").slice(1);
    const selected = rows.find((r) => r.getAttribute("aria-selected") === "true");
    expect(selected).toBeTruthy();
    expect(selected).toHaveTextContent("Alpha");
    expect(selected?.className).toContain("border-l-[var(--color-player-self)]");
  });

  it("sorts ascending then descending then back to default on repeated header clicks", () => {
    render(
      <PlanetList
        planets={planets}
        selectedPlanetId={null}
        onSelectPlanet={() => undefined}
        columns={[nameCol]}
      />,
    );
    const header = screen.getByRole("columnheader", { name: /Name/ });

    // default: asc by name
    let rows = screen.getAllByRole("row").slice(1);
    expect(rows[0]).toHaveTextContent("Alpha");

    // click 1: set sort asc
    fireEvent.click(header);
    rows = screen.getAllByRole("row").slice(1);
    expect(rows[0]).toHaveTextContent("Alpha");

    // click 2: desc
    fireEvent.click(header);
    rows = screen.getAllByRole("row").slice(1);
    expect(rows[0]).toHaveTextContent("Zeta");

    // click 3: clear sort (back to unsorted = original array order = p1 Zeta, p2 Alpha, p3 Mars)
    fireEvent.click(header);
    rows = screen.getAllByRole("row").slice(1);
    expect(rows[0]).toHaveTextContent("Zeta"); // original insertion order
  });

  it("places null sortValues last regardless of direction", () => {
    const nullSortCol: PlanetListColumn = {
      id: "nulls",
      header: "N",
      sortable: true,
      sortValue: (p) => (p.name === "Mars" ? null : p.name),
      render: (p) => p.name,
    };
    render(
      <PlanetList
        planets={planets}
        selectedPlanetId={null}
        onSelectPlanet={() => undefined}
        columns={[nullSortCol]}
      />,
    );
    const header = screen.getByRole("columnheader", { name: /^N/ });

    // asc: first click resets cycle to asc (same as default)
    fireEvent.click(header);
    let rows = screen.getAllByRole("row").slice(1);
    expect(rows[rows.length - 1]).toHaveTextContent("Mars");

    // desc
    fireEvent.click(header);
    rows = screen.getAllByRole("row").slice(1);
    expect(rows[rows.length - 1]).toHaveTextContent("Mars");
  });

  it("filters rows case-insensitively by search string", () => {
    const filter: PlanetListFilter = {
      search: "al",
      toggles: [],
      onChange: () => undefined,
    };
    render(
      <PlanetList
        planets={planets}
        selectedPlanetId={null}
        onSelectPlanet={() => undefined}
        columns={[nameCol]}
        filter={filter}
      />,
    );
    const rows = screen.getAllByRole("row").slice(1);
    expect(rows).toHaveLength(1);
    expect(rows[0]).toHaveTextContent("Alpha");
  });

  it("shows the empty-filter message and calls filter.onChange with reset values on clear", () => {
    const onChange = vi.fn();
    const filter: PlanetListFilter = {
      search: "xyzzy",
      toggles: [{ id: "t1", label: "T1", active: true }],
      onChange,
    };
    render(
      <PlanetList
        planets={planets}
        selectedPlanetId={null}
        onSelectPlanet={() => undefined}
        columns={[nameCol]}
        filter={filter}
      />,
    );
    expect(screen.getByText("No planets match the current filter.")).toBeTruthy();
    fireEvent.click(screen.getByText("Clear filter"));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ search: "", toggles: [{ id: "t1", label: "T1", active: false }] }),
    );
  });

  it("does not sort when a non-sortable column header is clicked", () => {
    render(
      <PlanetList
        planets={planets}
        selectedPlanetId={null}
        onSelectPlanet={() => undefined}
        columns={[noSortCol, nameCol]}
      />,
    );
    fireEvent.click(screen.getByText("Fixed"));
    // Clicking a non-sortable column does not change the active sort (name asc remains)
    const rows = screen.getAllByRole("row").slice(1);
    expect(rows[0]).toHaveTextContent("Alpha"); // name-sorted asc, unchanged by Fixed click
  });
});
