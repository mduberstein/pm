import { expect, test } from "@playwright/test";

const baselineBoard = {
  columns: [
    { id: "col-backlog", title: "Backlog", cardIds: ["card-1", "card-2"] },
    { id: "col-discovery", title: "Discovery", cardIds: ["card-3"] },
    { id: "col-progress", title: "In Progress", cardIds: ["card-4", "card-5"] },
    { id: "col-review", title: "Review", cardIds: ["card-6"] },
    { id: "col-done", title: "Done", cardIds: ["card-7", "card-8"] },
  ],
  cards: {
    "card-1": {
      id: "card-1",
      title: "Align roadmap themes",
      details: "Draft quarterly themes with impact statements and metrics.",
    },
    "card-2": {
      id: "card-2",
      title: "Gather customer signals",
      details: "Review support tags, sales notes, and churn feedback.",
    },
    "card-3": {
      id: "card-3",
      title: "Prototype analytics view",
      details: "Sketch initial dashboard layout and key drill-downs.",
    },
    "card-4": {
      id: "card-4",
      title: "Refine status language",
      details: "Standardize column labels and tone across the board.",
    },
    "card-5": {
      id: "card-5",
      title: "Design card layout",
      details: "Add hierarchy and spacing for scanning dense lists.",
    },
    "card-6": {
      id: "card-6",
      title: "QA micro-interactions",
      details: "Verify hover, focus, and loading states.",
    },
    "card-7": {
      id: "card-7",
      title: "Ship marketing page",
      details: "Final copy approved and asset pack delivered.",
    },
    "card-8": {
      id: "card-8",
      title: "Close onboarding sprint",
      details: "Document release notes and share internally.",
    },
  },
};

const resetBoardViaApi = async (page: import("@playwright/test").Page) => {
  const loginResponse = await page.request.post("/api/auth/login", {
    data: {
      username: "user",
      password: "password",
    },
  });
  expect(loginResponse.ok()).toBeTruthy();

  const loginJson = (await loginResponse.json()) as { access_token?: string };
  const token = loginJson.access_token;
  if (!token) {
    throw new Error("No access token returned by auth API.");
  }

  const response = await page.request.put("/api/board", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    data: baselineBoard,
  });

  expect(response.ok()).toBeTruthy();
};

const login = async (page: import("@playwright/test").Page) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Sign in to Kanban Studio" })
  ).toBeVisible();
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await resetBoardViaApi(page);
  await page.reload();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
};

test("shows login first and then loads the kanban board", async ({ page }) => {
  await login(page);
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("rejects invalid credentials", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("wrong");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByText("Invalid username or password.")).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(0);
});

test("allows logout", async ({ page }) => {
  await login(page);
  await page.getByRole("button", { name: "Log out" }).click();
  await expect(
    page.getByRole("heading", { name: "Sign in to Kanban Studio" })
  ).toBeVisible();
});

test("adds a card to a column", async ({ page }) => {
  await login(page);
  const title = `Playwright card ${Date.now()}`;
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill(title);
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText(title)).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await login(page);

  const movedBoard = {
    ...baselineBoard,
    columns: baselineBoard.columns.map((column) => {
      if (column.id === "col-backlog") {
        return {
          ...column,
          cardIds: column.cardIds.filter((cardId) => cardId !== "card-1"),
        };
      }

      if (column.id === "col-review") {
        return {
          ...column,
          cardIds: ["card-1", ...column.cardIds],
        };
      }

      return column;
    }),
  };

  const loginResponse = await page.request.post("/api/auth/login", {
    data: {
      username: "user",
      password: "password",
    },
  });
  expect(loginResponse.ok()).toBeTruthy();

  const loginJson = (await loginResponse.json()) as { access_token?: string };
  const token = loginJson.access_token;
  if (!token) {
    throw new Error("No access token returned by auth API.");
  }

  const updateResponse = await page.request.put("/api/board", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    data: movedBoard,
  });
  expect(updateResponse.ok()).toBeTruthy();

  await page.reload();
  const targetColumn = page.getByTestId("column-col-review");
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});

test("persists board changes across refresh", async ({ page }) => {
  await login(page);

  const title = `Persistent card ${Date.now()}`;
  const firstColumn = page.locator('[data-testid^="column-"]').first();

  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill(title);
  await firstColumn.getByPlaceholder("Details").fill("Persists via backend API.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText(title)).toBeVisible();

  await page.reload();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.getByText(title)).toBeVisible();
});

test("applies AI chat board updates without manual reload", async ({ page }) => {
  await login(page);

  await page.route("**/api/chat", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        assistant: "Applied your update.",
        board: {
          columns: [
            {
              id: "col-backlog",
              title: "Backlog",
              cardIds: ["card-1"],
            },
          ],
          cards: {
            "card-1": {
              id: "card-1",
              title: "Updated by AI",
              details: "Changed through chat response",
            },
          },
        },
      }),
    });
  });

  await page.getByLabel("Message").fill("Update the first card title");
  await page.getByRole("button", { name: "Send to AI" }).click();

  await expect(page.getByText("Applied your update.")).toBeVisible();
  await expect(page.getByText("Updated by AI")).toBeVisible();
});
