import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DesignsWorkspace } from "./DesignsWorkspace";

const mockGetDesignerReferenceData = vi.hoisted(() => vi.fn());
const mockGetDesigns = vi.hoisted(() => vi.fn());
const mockGetDesignDetail = vi.hoisted(() => vi.fn());
const mockCreateDesign = vi.hoisted(() => vi.fn());

vi.mock("../api/client", () => ({
  ApiError: class ApiError extends Error {
    status: number;
    code: string;
    constructor(status: number, code: string, message: string) {
      super(message);
      this.status = status;
      this.code = code;
    }
  },
  getDesignerReferenceData: mockGetDesignerReferenceData,
  getDesigns: mockGetDesigns,
  getDesignDetail: mockGetDesignDetail,
  createDesign: mockCreateDesign,
}));

const referenceData = {
  domain: "ship" as const,
  hulls: [
    {
      id: "scout",
      name: "Scout",
      cost: { resources: 20, ironium: 12, boranium: 0, germanium: 17 },
      mass: 25,
      domain: "ship" as const,
      fuelCapacity: 50,
      cargoCapacity: 0,
      dockCapacity: 0,
      armourPoints: 5,
      initiative: 0,
      slots: [
        {
          slotNumber: 1,
          slotCategories: ["engine"] as const,
          capacity: 1,
          required: true,
        },
        {
          slotNumber: 2,
          slotCategories: ["scanner"] as const,
          capacity: 1,
          required: false,
        },
      ],
    },
  ],
  components: [
    {
      id: "trans_galactic_drive",
      name: "Trans-Galactic Drive",
      componentType: "engine" as const,
      cost: { resources: 8, ironium: 2, boranium: 0, germanium: 2 },
      mass: 4,
      engine: { fuelUsage: [5, 10, 15, 20, 25, 30, 35, 40, 45, 50], isRamscoop: false },
    },
    {
      id: "rhino_scanner",
      name: "Rhino Scanner",
      componentType: "scanner" as const,
      cost: { resources: 5, ironium: 3, boranium: 0, germanium: 2 },
      mass: 3,
      scanner: { normal: 120, penetrating: 0 },
    },
  ],
};

const startingDesignSummary = [
  {
    id: "DEseed1",
    name: "Scout",
    hull: "scout",
    fuelCapacity: 50,
    cost: { resources: 15, minerals: { ironium: 5, boranium: 3, germanium: 2 } },
  },
];

describe("DesignsWorkspace", () => {
  beforeEach(() => {
    mockGetDesignerReferenceData.mockReset();
    mockGetDesigns.mockReset();
    mockGetDesignDetail.mockReset();
    mockCreateDesign.mockReset();
    mockGetDesignerReferenceData.mockResolvedValue(referenceData);
    mockGetDesigns.mockResolvedValue(startingDesignSummary);
    mockGetDesignDetail.mockResolvedValue({
      design: {
        ...startingDesignSummary[0],
        fuelUsage: [5, 10, 15, 20, 25, 30, 35, 40, 45, 50],
        scanner: { normal: 0, penetrating: 0 },
        cargoCapacity: 0,
      },
    });
  });

  it("shows list and allows selecting read-only detail", async () => {
    render(<DesignsWorkspace gameId="game-1" player="tim" />);
    await waitFor(() => {
      expect(screen.getByText("Designs")).toBeInTheDocument();
    });
    expect(screen.getAllByText("Scout").length).toBeGreaterThan(0);
    expect(screen.getByText(/Hull: scout/i)).toBeInTheDocument();
  });

  it("shows unknown scanner and cargo when detail is unavailable", async () => {
    mockGetDesignDetail.mockRejectedValueOnce(new Error("detail unavailable"));
    render(<DesignsWorkspace gameId="game-1" player="tim" />);

    await waitFor(() => {
      expect(screen.getByText("Designs")).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole("button", { name: /scout/i })[0]);

    await waitFor(() => {
      expect(
        screen.getByText("Unable to load full design detail. Showing summary values."),
      ).toBeInTheDocument();
    });

    expect(screen.getByText("Scanner unknown • Cargo unknown")).toBeInTheDocument();
  });

  it("disables save when required slots are missing", async () => {
    render(<DesignsWorkspace gameId="game-1" player="tim" />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Create New" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Create New" }));
    fireEvent.change(screen.getByLabelText("Design name"), {
      target: { value: "Long Range Scout" },
    });

    const saveButton = screen.getByRole("button", { name: "Save Design" });
    expect(saveButton).toBeDisabled();
    expect(screen.queryByText(/Slot 1 \(Engine\) needs 1 engines/i)).not.toBeInTheDocument();
  });

  it("submits create flow and returns to list", async () => {
    mockCreateDesign.mockResolvedValue({
      design: {
        id: "DEnew1",
        owner: "tim",
        name: "Long Range Scout",
        hull: "scout",
        fuelUsage: [5, 10, 15, 20, 25, 30, 35, 40, 45, 50],
        fuelCapacity: 50,
        scanner: { normal: 120, penetrating: 0 },
        cargoCapacity: 0,
        cost: { resources: 23, minerals: { ironium: 7, boranium: 0, germanium: 4 } },
      },
    });
    mockGetDesigns.mockResolvedValueOnce(startingDesignSummary).mockResolvedValueOnce([
      ...startingDesignSummary,
      {
        id: "DEnew1",
        name: "Long Range Scout",
        hull: "scout",
        fuelCapacity: 50,
        cost: { resources: 23, minerals: { ironium: 7, boranium: 0, germanium: 4 } },
      },
    ]);
    mockGetDesignDetail.mockResolvedValue({
      design: {
        id: "DEnew1",
        owner: "tim",
        name: "Long Range Scout",
        hull: "scout",
        fuelUsage: [5, 10, 15, 20, 25, 30, 35, 40, 45, 50],
        fuelCapacity: 50,
        scanner: { normal: 120, penetrating: 0 },
        cargoCapacity: 0,
        cost: { resources: 23, minerals: { ironium: 7, boranium: 0, germanium: 4 } },
      },
    });

    render(<DesignsWorkspace gameId="game-1" player="tim" />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Create New" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Create New" }));
    fireEvent.change(screen.getByLabelText("Design name"), {
      target: { value: "Long Range Scout" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Trans-Galactic Drive/i }));
    fireEvent.keyDown(screen.getByRole("button", { name: "Engine fitting cell" }), {
      key: "Enter",
    });
    fireEvent.click(screen.getByRole("tab", { name: "Scanners" }));
    fireEvent.click(screen.getByRole("button", { name: /Rhino Scanner/i }));
    fireEvent.keyDown(screen.getByRole("button", { name: "Scanner fitting cell" }), {
      key: "Enter",
    });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Save Design" })).toBeEnabled();
    });
    fireEvent.click(screen.getByRole("button", { name: "Save Design" }));

    await waitFor(() => {
      expect(mockCreateDesign).toHaveBeenCalledWith(
        "game-1",
        "tim",
        expect.objectContaining({
          name: "Long Range Scout",
          hull: "scout",
          components: expect.arrayContaining([
            expect.objectContaining({
              slotNumber: 1,
              componentId: "trans_galactic_drive",
              componentCount: 1,
            }),
          ]),
        }),
      );
    });

    await waitFor(() => {
      expect(screen.getAllByText("Long Range Scout").length).toBeGreaterThan(0);
    });
  });
});
