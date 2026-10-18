import { signUp } from "aws-amplify/auth";
import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authErrorMessage } from "@/auth/errors";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import TextField from "@/components/ui/TextField";
import AuthLayout from "../components/AuthLayout";

// Sign up (US-01). Cognito emails a code, confirmed on /confirm.
export default function SignUpPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    const username = email.trim();
    try {
      const { nextStep } = await signUp({
        username,
        password,
        options: { userAttributes: { email: username, name: name.trim() }, autoSignIn: true },
      });
      if (nextStep.signUpStep === "CONFIRM_SIGN_UP") {
        navigate("/confirm", { state: { email: username, autoSignIn: true } });
      } else {
        navigate("/login", { state: { email: username, message: "Account created. Log in to continue." } });
      }
    } catch (err) {
      setError(authErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Your campaigns and creators are private to you."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-brand hover:underline">
            Log in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
        {error && <Alert>{error}</Alert>}
        <TextField
          label="Name"
          autoComplete="name"
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
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
          autoComplete="new-password"
          required
          minLength={8}
          hint="At least 8 characters, with upper and lower case letters and a number."
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <Button type="submit" loading={submitting} disabled={!name || !email || !password}>
          Create account
        </Button>
      </form>
    </AuthLayout>
  );
}
