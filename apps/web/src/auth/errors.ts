// Turns Cognito errors into messages a manager can act on.

const MESSAGES: Record<string, string> = {
  NotAuthorizedException: "Incorrect email or password.",
  UserNotFoundException: "Incorrect email or password.",
  UsernameExistsException: "An account with this email already exists. Try logging in.",
  CodeMismatchException: "That code is incorrect. Check the email and try again.",
  ExpiredCodeException: "That code has expired. Request a new one.",
  LimitExceededException: "Too many attempts. Wait a few minutes and try again.",
  TooManyRequestsException: "Too many attempts. Wait a few minutes and try again.",
  NetworkError: "Can't reach the sign-in service. Check your connection.",
};

export function authErrorMessage(error: unknown): string {
  if (error instanceof Error) return MESSAGES[error.name] ?? error.message;
  return "Something went wrong. Please try again.";
}
