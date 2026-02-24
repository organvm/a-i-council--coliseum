import { test, expect } from '@playwright/test';

test('has title and renders active council', async ({ page }) => {
  await page.goto('/');

  // Expect a heading for the Active Council
  await expect(page.getByRole('heading', { name: 'Active Council' })).toBeVisible();
  
  // Expect a heading for the Arena3D
  await expect(page.getByText('Uptime:')).toBeVisible();
  
  // Expect the Canvas element to be present (from Area3D)
  const canvas = page.locator('canvas');
  await expect(canvas.first()).toBeVisible();
});
