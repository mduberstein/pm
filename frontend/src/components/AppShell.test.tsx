import { render, screen, waitFor } from "@testing-library/react";
import { AppShell } from "@/components/AppShell";

describe("AppShell", () => {
  it("shows sign in when no auth token exists", async () => {
    window.localStorage.removeItem("pm_auth_token");

    render(<AppShell />);

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Sign in to Kanban Studio" })
      ).toBeInTheDocument();
    });
  });
});
