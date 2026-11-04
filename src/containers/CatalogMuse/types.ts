export type Marketplace = "amazon" | "walmart";

export type JobAgent = {
  name: string;
  state?: string;
  detail?: string;
  output?: Record<string, unknown> | null;
};

export type Job = {
  id: string;
  status?: string;
  error?: string;
  marketplaces?: string[];
  pending_agent?: string | null;
  approve_allowed?: boolean;
  agents?: JobAgent[];
};

export type SceneImage = {
  file: string;
  url?: string;
  prompt?: string;
  style?: number;
  variation?: number;
};

export type ListingCopy = {
  title: string;
  bullets: string[];
  description: string;
  shortDescription: string;
  shelfDescription: string;
};

export type CatalogItem = {
  id: string;
  title: string;
  date: string;
  imageCount: number;
  marketplaces: string[];
  imageUrl?: string;
};

export function agentOutput(job: Job | null, name: string) {
  const output = job?.agents?.find((agent) => agent.name === name)?.output;
  if (!output || typeof output !== "object") return undefined;
  return output;
}

export function jobMarketplaces(job: Job | null): Marketplace[] {
  const selected = (job?.marketplaces ?? []).filter(
    (item): item is Marketplace => item === "amazon" || item === "walmart",
  );
  return selected.length > 0 ? selected : ["amazon"];
}

export function asLines(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.map((item) => String(item)).filter(Boolean);
  }
  if (typeof value === "string") {
    return value
      .split("\n")
      .map((line) => line.replace(/^[-•]\s*/, "").trim())
      .filter(Boolean);
  }
  return [];
}

export function cutoutSource(job: Job | null) {
  const output = agentOutput(job, "segment");
  if (!output) return null;
  const file = typeof output.file === "string" ? output.file : undefined;
  const url = typeof output.url === "string" ? output.url : undefined;
  if (!file && !url) return null;
  return { file, url };
}

export function artStyles(job: Job | null): string[] {
  const styles = agentOutput(job, "art_director")?.styles;
  if (!Array.isArray(styles)) return [];
  return styles.map((style) => String(style)).filter(Boolean);
}

function readSceneImages(value: unknown): SceneImage[] {
  if (!Array.isArray(value)) return [];
  return value.flatMap((item) => {
    if (typeof item === "string" && item) return [{ file: item }];
    if (!item || typeof item !== "object") return [];
    const record = item as Record<string, unknown>;
    const file = String(record.file ?? record.name ?? "");
    if (!file) return [];
    const url = typeof record.url === "string" ? record.url : undefined;
    const prompt = typeof record.prompt === "string" ? record.prompt : undefined;
    const style = typeof record.style === "number" ? record.style : undefined;
    const variation = typeof record.variation === "number" ? record.variation : undefined;
    return [{ file, url, prompt, style, variation }];
  });
}

export function sceneImages(job: Job | null): SceneImage[] {
  const output = agentOutput(job, "scene");
  if (!output) return [];
  const images = readSceneImages(output.images);
  const scene = job?.agents?.find((agent) => agent.name === "scene");
  const chosen = scene?.state === "approved" || job?.status === "approved";
  const selected = asLines(output.selected);
  if (!chosen || selected.length === 0) return images;
  const byFile = new Map(images.map((image) => [image.file, image]));
  const primaryUrl = typeof output.url === "string" ? output.url : undefined;
  const primaryFile = typeof output.file === "string" ? output.file : "";
  return selected.map(
    (file) =>
      byFile.get(file) ?? {
        file,
        url: file === primaryFile ? primaryUrl : undefined,
      },
  );
}

export function violations(job: Job | null): string[] {
  const list = agentOutput(job, "rules")?.violations;
  if (!Array.isArray(list)) return [];
  return list.map((item) => {
    if (typeof item === "string") return item;
    if (item && typeof item === "object") {
      const record = item as Record<string, unknown>;
      return String(record.message ?? record.text ?? JSON.stringify(item));
    }
    return String(item);
  });
}

function textField(record: Record<string, unknown>, key: string) {
  return typeof record[key] === "string" ? record[key] : "";
}

function readListing(record: Record<string, unknown>, walmart = false): ListingCopy | null {
  const title = textField(record, "title");
  const description = textField(record, walmart ? "shelf_description" : "description");
  const shortDescription = textField(record, "short_description");
  const bullets = asLines(record.bullets ?? record.features ?? record.bullet_points);
  if (!title && !description && !shortDescription && bullets.length === 0) return null;
  return { title, bullets, description, shortDescription, shelfDescription: description };
}

export function listingCopy(job: Job | null, marketplace: Marketplace) {
  const output = agentOutput(job, "copy");
  if (!output) return null;
  if (marketplace === "walmart") {
    const walmart = output.walmart;
    if (!walmart || typeof walmart !== "object") return null;
    return readListing(walmart as Record<string, unknown>, true);
  }
  return readListing(output);
}

export function ruleViolations(job: Job | null, marketplace: Marketplace) {
  const section = agentOutput(job, "rules")?.[marketplace];
  if (!section || typeof section !== "object") return [];
  return asLines((section as Record<string, unknown>).violations);
}

const PIPELINE = ["segment", "art_director", "scene", "copy", "rules"] as const;

function agentStep(name: string) {
  switch (name) {
    case "segment":
      return 2;
    case "art_director":
    case "scene":
      return 3;
    case "copy":
    case "rules":
      return 4;
    default:
      return 0;
  }
}

export function viewStep(job: Job | null) {
  if (!job) return 1;
  if (job.status === "approved") return 5;
  if (job.pending_agent) {
    const pending = agentStep(job.pending_agent);
    if (pending) return pending;
  }
  const agents = job.agents ?? [];
  for (const name of PIPELINE) {
    const agent = agents.find((item) => item.name === name);
    if (!agent || agent.state !== "approved") return agentStep(name);
  }
  return 4;
}

export function jobStatusLabel(job: Job) {
  if (job.status === "approved") return "Approved";
  if (job.status === "failed") return "Failed";
  switch (job.pending_agent) {
    case "segment":
      return "Waiting for cutout approval";
    case "art_director":
      return "Waiting for style approval";
    case "scene":
      return "Waiting for image selection";
    case "copy":
    case "rules":
      return "Waiting for listing approval";
    default:
      return job.status === "running" ? "Working" : job.status || "Loading";
  }
}

export function isWorking(job: Job | null) {
  return Boolean(
    job &&
      job.status !== "approved" &&
      job.status !== "failed" &&
      !job.pending_agent,
  );
}
