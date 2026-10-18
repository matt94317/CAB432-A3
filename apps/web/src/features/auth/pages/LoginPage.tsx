import { signIn } from "aws-amplify/auth";
import { type FormEvent, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/auth/AuthProvider";
import { authErrorMessage } from "@/auth/errors";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import TextField from "@/components/ui/TextField";
import AuthLayout from "../components/AuthLayout";

interface LoginState {
  from?: string;
  email?: string;
  message?: string;
}

// Log in (US-01).
export default function LoginPage() {
  const navigate = useNavigate();
  const { refresh } = useAuth();
  const state = (useLocation().state ?? {}) as LoginState;

  const [email, setEmail] = useState(state.email ?? "");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const { nextStep } = await signIn({ username: email.trim(), password });
      if (nextStep.signInStep === "CONFIRM_SIGN_UP") {
        navigate("/confirm", { state: { email: email.trim() } });
        return;
      }
      if (nextStep.signInStep !== "DONE") {
        setError("This account needs a sign-in step the app doesn't support yet.");
        return;
      }
      await refresh();
      navigate(state.from ?? "/campaigns", { replace: true });
    } catch (err) {
      setError(authErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout
      title="Log in"
      subtitle="Track every creator and post in one place."
      footer={
        <>
          New to Hookd Tracker?{" "}
          <Link to="/signup" className="font-medium text-brand hover:underline">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
        {state.message && !error && <Alert tone="success">{state.message}</Alert>}
        {error && <Alert>{error}</Alert>}
        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <TextField
          label="Password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <Button type="submit" loading={submitting} disabled={!email || !password}>
          Log in
        </Button>
      </form>
    </AuthLayout>
  );
}
