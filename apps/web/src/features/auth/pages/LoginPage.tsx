import { signIn } from "aws-amplify/auth";
import { type FormEvent, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/auth/AuthProvider";
import { authErrorMessage } from "@/auth/errors";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import TextField from "@/components/ui/TextField";
import AuthLayout from "../components/AuthLayout";
import PasswordField from "../components/PasswordField";

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
      eyebrow="GOOD TO HAVE YOU BACK"
      title="Your people. Your place."
      subtitle="Log in to keep the good collaborations going."
      footer={
        <>
          New around here?{" "}
          <Link to="/signup" className="font-semibold text-brand hover:underline">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-5" noValidate>
        {state.message && !error && <Alert tone="success">{state.message}</Alert>}
        {error && <Alert>{error}</Alert>}
        <TextField
          label="Work email"
          type="email"
          autoComplete="email"
          fieldSize="lg"
          placeholder="you@company.com"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <PasswordField
          label="Password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <Button type="submit" icon="arrow-right" loading={submitting} disabled={!email || !password}>
          Log in to Hookd
        </Button>
      </form>
    </AuthLayout>
  );
}
