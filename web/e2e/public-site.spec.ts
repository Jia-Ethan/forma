import { expect, test } from "@playwright/test";

test("public site and demo are reachable", async ({ page }) => {
  await page.route("**/api/health", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        app_env: "e2e",
        template: "sc-th-word",
        capabilities: { docx_export: true, profile: "undergraduate" },
        limits: { max_docx_size_bytes: 20 * 1024 * 1024, max_text_precheck_chars: 80_000 },
      }),
    });
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "华师本科论文格式合规与版本工作台" })).toBeVisible();
  await expect(page.getByRole("link", { name: "English" })).toBeVisible();
  await expect(page.getByPlaceholder("粘贴已有论文正文进行格式预检")).toBeVisible();

  await page.getByRole("link", { name: "English" }).click();
  await expect(page.getByRole("heading", { name: "SCNU undergraduate thesis formatting and export workbench" })).toBeVisible();

  await page.goto("/#/workbench-demo");
  await expect(page.getByRole("heading", { name: "SCNU Thesis Agent Workbench Demo" })).toBeVisible();
  await page.getByRole("button", { name: "模拟导出" }).click();
  await expect(page.getByText("demo-export-4.docx")).toBeVisible();
  await page.getByRole("button", { name: "重置 demo" }).click();
  await expect(page.getByText("demo-export-4.docx")).toHaveCount(0);
});
