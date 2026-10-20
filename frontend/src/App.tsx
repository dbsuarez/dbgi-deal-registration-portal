import {
  Alert,
  AppBar,
  Box,
  Button,
  CircularProgress,
  Stack,
  Toolbar,
  Typography,
} from "@mui/material";
import { lazy, Suspense, useEffect, useState } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { getSession, logoutSession, type Session } from "./api";
import { SessionContext } from "./session";

const RegistrationListPage = lazy(() => import("./pages/RegistrationListPage"));
const RegistrationDetailPage = lazy(
  () => import("./pages/RegistrationDetailPage"),
);
const RegistrationFormPage = lazy(() => import("./pages/RegistrationFormPage"));
const OpportunityRankingsPage = lazy(
  () => import("./pages/OpportunityRankingsPage"),
);

function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [sessionError, setSessionError] = useState("");
  const [sessionAttempt, setSessionAttempt] = useState(0);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    getSession(controller.signal)
      .then(setSession)
      .catch((reason: Error) => {
        if (reason.name === "AbortError") return;
        setSessionError(
          reason.message || "The portal could not reach the server.",
        );
      });
    return () => controller.abort();
  }, [sessionAttempt]);

  if (sessionError && !session) {
    return (
      <Box sx={{ display: "grid", minHeight: "100vh", placeItems: "center" }}>
        <Stack spacing={2} alignItems="center" sx={{ maxWidth: 480, px: 3 }}>
          <Alert severity="error">{sessionError}</Alert>
          <Button
            variant="contained"
            onClick={() => {
              setSessionError("");
              setSessionAttempt((attempt) => attempt + 1);
            }}
          >
            Try again
          </Button>
        </Stack>
      </Box>
    );
  }

  if (!session) {
    return (
      <Box sx={{ display: "grid", minHeight: "100vh", placeItems: "center" }}>
        <CircularProgress aria-label="Loading portal" />
      </Box>
    );
  }

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await logoutSession(session.csrf_token);
      window.location.assign("/accounts/login/");
    } catch {
      setIsLoggingOut(false);
    }
  };

  return (
    <SessionContext.Provider value={session}>
      <BrowserRouter>
        <Box
          sx={{ display: "flex", minHeight: "100vh", flexDirection: "column" }}
        >
          <AppBar position="static">
            <Toolbar>
              <Typography
                variant="h6"
                component="a"
                href="/"
                color="inherit"
                sx={{ flexGrow: 1 }}
              >
                DBGI Project Registration
              </Typography>
              <Typography sx={{ mr: 2 }}>{session.display_name}</Typography>
              <Button color="inherit" href="/rankings/">
                Rankings
              </Button>
              {session.is_dbgi_admin && (
                <Button color="inherit" href="/admin/">
                  Administration
                </Button>
              )}
              <Button
                color="inherit"
                disabled={isLoggingOut}
                onClick={handleLogout}
              >
                {isLoggingOut ? "Logging out..." : "Log out"}
              </Button>
            </Toolbar>
          </AppBar>
          <Box component="main" sx={{ flexGrow: 1 }}>
            <Suspense
              fallback={
                <Box
                  sx={{ display: "grid", minHeight: 400, placeItems: "center" }}
                >
                  <CircularProgress aria-label="Loading page" />
                </Box>
              }
            >
              <Routes>
                <Route path="/" element={<RegistrationListPage />} />
                <Route
                  path="/registrations/new/"
                  element={<RegistrationFormPage />}
                />
                <Route
                  path="/registrations/:id/"
                  element={<RegistrationDetailPage />}
                />
                <Route
                  path="/registrations/:id/edit/"
                  element={<RegistrationFormPage />}
                />
                <Route
                  path="/rankings/"
                  element={<OpportunityRankingsPage />}
                />
              </Routes>
            </Suspense>
          </Box>
          <Box component="footer" sx={{ px: 3, py: 1.5, textAlign: "center" }}>
            <Typography variant="caption" color="text.secondary">
              Build: {__BUILD_TIME__}
            </Typography>
          </Box>
        </Box>
      </BrowserRouter>
    </SessionContext.Provider>
  );
}

export default App;
