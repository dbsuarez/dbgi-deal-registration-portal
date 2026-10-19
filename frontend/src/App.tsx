import {
  AppBar,
  Box,
  Button,
  CircularProgress,
  Toolbar,
  Typography,
} from "@mui/material";
import { lazy, Suspense, useEffect, useState } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { getSession, type Session } from "./api";
import { SessionContext } from "./session";

const RegistrationListPage = lazy(() => import("./pages/RegistrationListPage"));
const RegistrationDetailPage = lazy(
  () => import("./pages/RegistrationDetailPage"),
);
const RegistrationFormPage = lazy(() => import("./pages/RegistrationFormPage"));

function App() {
  const [session, setSession] = useState<Session | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getSession(controller.signal)
      .then(setSession)
      .catch(() => undefined);
    return () => controller.abort();
  }, []);

  if (!session) {
    return (
      <Box sx={{ display: "grid", minHeight: "100vh", placeItems: "center" }}>
        <CircularProgress aria-label="Loading portal" />
      </Box>
    );
  }

  return (
    <SessionContext.Provider value={session}>
      <BrowserRouter>
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
            {session.is_dbgi_admin && (
              <Button color="inherit" href="/admin/">
                Administration
              </Button>
            )}
            <Box component="form" method="post" action="/accounts/logout/">
              <input
                type="hidden"
                name="csrfmiddlewaretoken"
                value={session.csrf_token}
              />
              <Button color="inherit" type="submit">
                Log out
              </Button>
            </Box>
          </Toolbar>
        </AppBar>
        <Suspense
          fallback={
            <Box sx={{ display: "grid", minHeight: 400, placeItems: "center" }}>
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
          </Routes>
        </Suspense>
      </BrowserRouter>
    </SessionContext.Provider>
  );
}

export default App;
