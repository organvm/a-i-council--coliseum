#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";

async function loadChromium() {
  try {
    const mod = await import("@playwright/test");
    return mod.chromium;
  } catch {
    const fallbackUrl = new URL("../frontend/node_modules/@playwright/test/index.mjs", import.meta.url);
    const mod = await import(fallbackUrl.href);
    return mod.chromium;
  }
}

const apiUrl = process.env.API_URL || "http://localhost:8000";
const frontendUrl = process.env.FRONTEND_URL || "http://localhost:3000";
const scenario = process.env.SCENARIO || "ars_submission_showcase";
const durationSeconds = Number(process.env.DURATION_SECONDS || "180");
const speedMultiplier = Number(process.env.SPEED_MULTIPLIER || "1.0");
const headless = process.env.HEADLESS !== "false";
const outputDir = process.env.OUTPUT_DIR || path.resolve("output/playwright");

function withArena3DOverride(urlString, mode) {
  const url = new URL(urlString);
  url.searchParams.set("arena3d", mode);
  return url.toString();
}

async function probeWebGLSupport(page) {
  await page.goto("about:blank", { waitUntil: "domcontentloaded", timeout: 10000 });
  return page.evaluate(() => {
    const canvas = document.createElement("canvas");
    const tryContext = (name) => {
      try {
        return canvas.getContext(name);
      } catch {
        return null;
      }
    };

    const webgl2 = tryContext("webgl2");
    if (webgl2) {
      return { supported: true, context: "webgl2" };
    }

    const webgl = tryContext("webgl") || tryContext("experimental-webgl");
    if (webgl) {
      return { supported: true, context: "webgl" };
    }

    return { supported: false, context: null };
  });
}

async function startDirectorScenario() {
  const resp = await fetch(`${apiUrl}/api/demo/scenarios/${scenario}/start`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      restart_if_running: true,
      speed_multiplier: speedMultiplier,
    }),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Scenario start failed (${resp.status}): ${text}`);
  }

  const payload = await resp.json();
  const director = payload?.director ?? {};
  console.log("[record] director restart:", {
    scenario: director.scenario,
    status: director.status,
    run_id: director.run_id,
  });
}

async function main() {
  await fs.mkdir(outputDir, { recursive: true });

  await startDirectorScenario();

  const chromium = await loadChromium();
  const browser = await chromium.launch({ headless });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: { dir: outputDir, size: { width: 1920, height: 1080 } },
  });

  const page = await context.newPage();
  let sawWebGLContextFailure = false;
  page.on("console", (msg) => {
    const type = msg.type();
    if (type !== "error") {
      return;
    }

    const text = msg.text();
    if (
      text.includes("THREE.WebGLRenderer: A WebGL context could not be created") ||
      text.includes("THREE.WebGLRenderer: Error creating WebGL context")
    ) {
      if (!sawWebGLContextFailure) {
        sawWebGLContextFailure = true;
        console.log(
          "[record] WebGL renderer unavailable during capture; suppressing repeated THREE.WebGLRenderer errors (Arena3D should auto-fallback)."
        );
      }
      return;
    }

    console.log(`[record][browser:${type}] ${text}`);
  });

  let targetFrontendUrl = frontendUrl;
  try {
    const probe = await probeWebGLSupport(page);
    if (probe?.supported) {
      console.log(`[record] WebGL precheck: ${probe.context} available`);
    } else {
      targetFrontendUrl = withArena3DOverride(frontendUrl, "off");
      console.log(
        `[record] WebGL precheck: unavailable in recorder browser; forcing Arena3D off via URL override (${targetFrontendUrl})`
      );
    }
  } catch (err) {
    console.log("[record] WebGL precheck failed; continuing with configured Arena3D mode", err);
  }

  console.log(`[record] opening ${targetFrontendUrl}`);
  await page.goto(targetFrontendUrl, { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForTimeout(5000);

  console.log(`[record] capturing ${durationSeconds}s at 1920x1080`);
  await page.waitForTimeout(durationSeconds * 1000);

  const video = page.video();
  await page.close();
  await context.close();
  await browser.close();

  if (!video) {
    throw new Error("Playwright did not provide a recorded video handle");
  }

  const sourcePath = await video.path();
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const targetPath = path.join(outputDir, `final-take-${timestamp}.webm`);
  await fs.rename(sourcePath, targetPath);

  console.log("[record] video saved:", targetPath);
}

main().catch((err) => {
  console.error("[record] failed:", err);
  process.exit(1);
});
