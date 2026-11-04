import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, Settings } from "lucide-react";
import { Link, Outlet, useNavigate, useParams } from "react-router-dom";
import {
  createJob,
  decide,
  errorMessage,
  getJob,
  readImageFile,
  watchJob,
} from "@/lib/catalogApi";
import { BrandLogo } from "./BrandLogo";
import { Cutout } from "./Cutout";
import { Intake } from "./Intake";
import { Lifestyle } from "./Lifestyle";
import { Review } from "./Review";
import { Seo } from "./Seo";
import { isWorking, jobStatusLabel, viewStep, type Job } from "./types";

const STEPS = ["Intake", "Cutout Approval", "Lifestyle Gen", "SEO & Compliance", "Final Review"];
const originalPhotos = new Map<string, string>();

export function CatalogShell() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-50 border-b border-slate-200 bg-white">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <Link to="/" className="rounded-md">
            <BrandLogo />
          </Link>
          <div className="flex items-center gap-4">
            <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
              Beta 1.0
            </span>
            <Settings size={20} className="text-slate-500" />
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}

export function PipelineHome() {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const submitIntake = (input: {
    spec: string;
    file: File;
    previewUrl: string;
    marketplaces: string[];
  }) => {
    void (async () => {
      setBusy(true);
      setError("");
      try {
        const image = await readImageFile(input.file);
        const created = await createJob(input.spec, image, input.marketplaces);
        originalPhotos.set(created.id, input.previewUrl);
        navigate(`/jobs/${created.id}`);
      } catch (caught) {
        setError(errorMessage(caught));
        setBusy(false);
      }
    })();
  };

  return (
    <>
      {error && <ErrorBanner message={error} />}
      <Intake busy={busy} onSubmit={submitIntake} />
    </>
  );
}

export function JobDetail() {
  const { jobId = "" } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState<Job | null>(null);
  const [awaitingEvent, setAwaitingEvent] = useState(false);
  const [error, setError] = useState("");
  const [stepOverride, setStepOverride] = useState<{ step: number; token: string } | null>(null);
  const submitted = useRef("");
  const awaitingRef = useRef(false);
  const closedRef = useRef(false);
  const stopWatch = useRef<() => void>(() => {});
  const stepToken = `${job?.id ?? ""}:${job?.pending_agent ?? ""}:${job?.status ?? ""}`;
  const derivedStep = viewStep(job);
  const step = job ? (stepOverride?.token === stepToken ? stepOverride.step : derivedStep) : 0;
  const working = awaitingEvent || isWorking(job);
  const stepError = error || (job?.status === "failed" ? job.error || "This job failed." : "");
  const originalUrl = originalPhotos.get(jobId) ?? "";

  const applyJob = useCallback((next: Job) => {
    setJob((current) => ({
      ...current,
      ...next,
      id: next.id || current?.id || jobId,
    }));
  }, [jobId]);

  useEffect(() => {
    if (!jobId) return;
    closedRef.current = false;
    getJob(jobId)
      .then((data) => {
        if (closedRef.current) return;
        setJob((current) => current ?? data);
      })
      .catch((caught: unknown) => {
        if (!closedRef.current) setError(errorMessage(caught));
      });
    const subscribe = () => {
      stopWatch.current();
      stopWatch.current = watchJob(
        jobId,
        (next) => {
          if (closedRef.current) return;
          applyJob(next);
          const mark = jobMark(next);
          if (submitted.current && mark !== submitted.current && !isWorking(next)) {
            submitted.current = "";
            awaitingRef.current = false;
            setAwaitingEvent(false);
          }
        },
        (message) => {
          if (closedRef.current) return;
          submitted.current = "";
          awaitingRef.current = false;
          setAwaitingEvent(false);
          setError(message);
        },
      );
    };
    subscribe();
    return () => {
      closedRef.current = true;
      stopWatch.current();
    };
  }, [applyJob, jobId]);

  const sendDecision = (body: Record<string, unknown>) => {
    if (awaitingRef.current || isWorking(job)) return;
    if (job?.status === "failed") {
      closedRef.current = false;
      stopWatch.current();
      stopWatch.current = watchJob(
        jobId,
        (next) => {
          if (closedRef.current) return;
          applyJob(next);
          const mark = jobMark(next);
          if (submitted.current && mark !== submitted.current && !isWorking(next)) {
            submitted.current = "";
            awaitingRef.current = false;
            setAwaitingEvent(false);
          }
        },
        (message) => {
          if (closedRef.current) return;
          submitted.current = "";
          awaitingRef.current = false;
          setAwaitingEvent(false);
          setError(message);
        },
      );
    }
    submitted.current = jobMark(job);
    awaitingRef.current = true;
    setAwaitingEvent(true);
    setError("");
    void decide(jobId, body).catch((caught: unknown) => {
      submitted.current = "";
      awaitingRef.current = false;
      setAwaitingEvent(false);
      setError(errorMessage(caught));
    });
  };

  return (
    <>
      <p className="mb-6 text-sm text-slate-500">
        Job {jobId}
        {job ? ` · ${jobStatusLabel(job)}` : ""}
      </p>
      <ol className="mb-10 grid grid-cols-5 gap-2">
        {STEPS.map((label, index) => {
          const number = index + 1;
          const active = number === step;
          const done = number < derivedStep;
          return (
            <li
              key={label}
              className={`border-t-2 pt-3 text-sm ${
                active
                  ? "border-blue-600 font-semibold text-blue-700"
                  : done
                    ? "border-blue-300 text-slate-700"
                    : "border-slate-200 text-slate-400"
              }`}
            >
              {number}. {label}
            </li>
          );
        })}
      </ol>
      {!job && !error && (
        <p className="rounded-md border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-800">
          Loading job {jobId}...
        </p>
      )}
      {working && (
        <p className="mb-4 flex items-center gap-2 rounded-md border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-800">
          <Loader2 size={16} className="animate-spin" />
          Catalog Muse is working. This step updates when the next status arrives.
        </p>
      )}
      {step === 2 && job && (
        <Cutout
          job={job}
          originalUrl={originalUrl}
          busy={working}
          error={stepError}
          onApprove={() => sendDecision({ action: "approve", agent: "segment" })}
          onRecut={(note) => sendDecision({ action: "changes", agent: "segment", note })}
          onCancel={() => navigate("/")}
        />
      )}
      {step === 3 && job && (
        <Lifestyle
          job={job}
          busy={working}
          onBack={() => setStepOverride({ step: 2, token: stepToken })}
          onGenerate={(styles, variations) =>
            sendDecision({ action: "approve", agent: "art_director", styles, variations })
          }
          onChooseImages={(images) => sendDecision({ action: "approve", agent: "scene", images })}
        />
      )}
      {step === 4 && job && (
        <Seo
          job={job}
          busy={working}
          onBack={() => setStepOverride({ step: 3, token: stepToken })}
          onApprove={() => sendDecision({ action: "approve", agent: "rules" })}
          onChange={(note) => sendDecision({ action: "changes", agent: "rules", note })}
        />
      )}
      {step === 5 && job && (
        <Review job={job} onRestart={() => navigate("/")} />
      )}
      {step !== 2 && stepError && <ErrorBanner message={stepError} />}
    </>
  );
}

function jobMark(job: Job | null) {
  const agents = (job?.agents ?? []).map((agent) => `${agent.name}:${agent.state ?? ""}`).join(",");
  return `${job?.status ?? ""}:${job?.pending_agent ?? ""}:${agents}`;
}

function ErrorBanner({ message }: { message: string }) {
  return (
    <p className="mt-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {message}
    </p>
  );
}
