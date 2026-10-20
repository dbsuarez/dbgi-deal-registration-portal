import { Button, Container, Stack, Typography } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <Container sx={{ py: 8 }}>
      <Stack spacing={2} alignItems="flex-start" sx={{ maxWidth: 560 }}>
        <Typography variant="overline" color="text.secondary">
          Error 404
        </Typography>
        <Typography component="h1" variant="h2">
          Page not found
        </Typography>
        <Typography color="text.secondary">
          The page may have moved, or the address may be incorrect.
        </Typography>
        <Button component={RouterLink} to="/" variant="contained">
          Go to registrations
        </Button>
      </Stack>
    </Container>
  );
}
