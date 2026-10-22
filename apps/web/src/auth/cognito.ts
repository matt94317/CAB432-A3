// Amplify / Cognito configuration (US-01, US-02).
//
// Amplify keeps the session in localStorage and silently refreshes the access
// token with the refresh token, so managers stay signed in between visits until
// they log out or the refresh token expires.
import { Amplify } from "aws-amplify";

const userPoolId = import.meta.env.VITE_COGNITO_USER_POOL_ID;
const userPoolClientId = import.meta.env.VITE_COGNITO_APP_CLIENT_ID;

export const authConfigured = Boolean(userPoolId && userPoolClientId);

export function configureAuth() {
  if (!authConfigured) return;
  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId,
        userPoolClientId,
        loginWith: { email: true },
        signUpVerificationMethod: "code",
      },
    },
  });
}
