import { autoSignIn, confirmSignUp, resendSignUpCode } from "aws-amplify/auth";
import { type FormEvent, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/auth/AuthProvider";
import { authErrorMessage } from "@/auth/errors";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import TextField from "@/components/ui/TextField";
import AuthLayout from "../components/AuthLayout";

interface ConfirmState {
  email?: string;
  autoSignIn?: boolean;
}

// Confirm the emailed sign-up code (US-01). Signs straight in when coming from sign-up.
export default function ConfirmSignUpPage() {
  const navigate = useNavigate();
  const { refresh } = useAuth();
  const state = (useLocation().state ?? {}) as ConfirmState;

  const [email, setEmail] = useState(state.email ?? "");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const goToLogin = () =>
    navigate("/login", {
      replace: true,
      state: { email, message: "Email confirmed. Log in to continue." },
    });

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setNotice(null);
    setSubmitting(true);
    try {
      const { nextStep } = await confirmSignUp({
        username: email.trim(),
        confirmationCode: code.trim(),
      });
      if (state.autoSignIn && nextStep.signUpStep === "COMPLETE_AUTO_SIGN_IN") {
        try {
          await autoSignIn();
          await refresh();
          navigate("/campaigns", { replace: true });
        } catch {
          goToLogin();
        }
        return;
      }
      goToLogin();
    } catch (err) {
      setError(authErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResend() {
    setError(null);
    setNotice(null);
    try {
      await resendSignUpCode({ username: email.trim() });
      setNotice(`We sent a new code to ${email.trim()}.`);
    } catch (err) {
      setError(authErrorMessage(err));
    }
  }

  return (
    <AuthLayout
      eyebrow="ONE LAST STEP"
      title="Check your email"
      subtitle={`Enter the 6-digit code we sent${email ? ` to ${email}` : ""} to confirm your account.`}
      footer={
        <Link to="/login" className="font-semibold text-brand hover:underline">
          Back to log in
        </Link>
      }
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-5" noValidate>
        {error && <Alert>{error}</Alert>}
        {notice && <Alert tone="success">{notice}</Alert>}
        {!state.email && (
          <TextField
            label="Work email"
            type="email"
            autoComplete="email"
            fieldSize="lg"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        )}
        <TextField
          label="Confirmation code"
          inputMode="numeric"
          autoComplete="one-time-code"
          fieldSize="lg"
          required
          value={code}
          onChange={(e) => setCode(e.target.value)}
        />
        <Button type="submit" loading={submitting} disabled={!email || !code}>
          Confirm email
        </Button>
        <Button type="button" variant="link" onClick={handleResend} disabled={!email}>
          Resend code
        </Button>
      </form>
    </AuthLayout>
  );
}
