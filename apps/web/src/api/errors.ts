// Turns API error bodies (FastAPI {detail}) into readable messages.

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface ValidationIssue {
  loc?: (string | number)[];
  msg?: string;
}

function describeIssue(issue: ValidationIssue): string {
  const message = (issue.msg ?? "Invalid value").replace(/^Value error, /, "");
  const field = issue.loc?.filter((part) => part !== "body").join(".");
  return field ? `${field.replaceAll("_", " ")}: ${message}` : message;
}

function messageFor(error: unknown, status: number): string {
  const detail = (error as { detail?: unknown } | undefined)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) return detail.map(describeIssue).join(". ");
  if (status === 401) return "Your session has expired. Log in again.";
  return `Something went wrong (${status}). Please try again.`;
}

/** Await an openapi-fetch call and return its data, or throw an ApiError. */
export async function unwrap<T>(
  request: Promise<{ data?: T; error?: unknown; response: Response }>,
): Promise<T> {
  const { data, error, response } = await request;
  if (!response.ok || error !== undefined) throw new ApiError(messageFor(error, response.status), response.status);
  return data as T;
}
