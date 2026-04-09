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
      domain: "ship" as const,
      engineRequiredSlots: 1,
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
      engine: { maxWarp: 8, isRamscoop: false },
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
    speed: 6,
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
    mockGetDesignDetail.mockResolvedValue({ design: startingDesignSummary[0] });
  });

  it("shows list and allows selecting read-only detail", async () => {
    render(<DesignsWorkspace gameId="game-1" player="tim" />);
    await waitFor(() => {
      expect(screen.getByText("Designs")).toBeInTheDocument();
    });
    expect(screen.getAllByText("Scout").length).toBeGreaterThan(0);
    expect(screen.getByText(/Hull: scout/i)).toBeInTheDocument();
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
    expect(screen.getByText(/Missing required slots/i)).toBeInTheDocument();
  });

  it("submits create flow and returns to list", async () => {
    mockCreateDesign.mockResolvedValue({
      design: {
        id: "DEnew1",
        owner: "tim",
        name: "Long Range Scout",
        hull: "scout",
        speed: 8,
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
        speed: 8,
        cost: { resources: 23, minerals: { ironium: 7, boranium: 0, germanium: 4 } },
      },
    ]);
    mockGetDesignDetail.mockResolvedValue({
      design: {
        id: "DEnew1",
        owner: "tim",
        name: "Long Range Scout",
        hull: "scout",
        speed: 8,
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
    fireEvent.change(screen.getByLabelText("Component slot 1"), {
      target: { value: "trans_galactic_drive" },
    });
    fireEvent.change(screen.getByLabelText("Component slot 2"), {
      target: { value: "rhino_scanner" },
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
