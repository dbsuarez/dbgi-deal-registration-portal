import {
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Chip,
  CircularProgress,
  Container,
  Link,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  getNotifications,
  markNotificationRead,
  type NotificationPage,
} from "../api";
import { useSession } from "../session";

function formatTimestamp(value: string) {
  return new Date(value).toLocaleString("sv-SE", {
    timeZone: "Asia/Manila",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function NotificationsPage() {
  const session = useSession();
  const navigate = useNavigate();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [data, setData] = useState<NotificationPage | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    getNotifications(page, pageSize, controller.signal)
      .then(setData)
      .catch((reason: Error) => {
        if (reason.name !== "AbortError") setError(reason.message);
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [page, pageSize]);

  const openNotification = async (
    notificationId: number,
    registrationId: number,
  ) => {
    try {
      await markNotificationRead(notificationId, session.csrf_token);
      navigate(`/registrations/${registrationId}/`);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The notification could not be opened.",
      );
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Breadcrumbs aria-label="Breadcrumb" sx={{ mb: 2 }}>
        <Link href="/">Registrations</Link>
        <Typography color="text.primary">Notifications</Typography>
      </Breadcrumbs>
      <Typography variant="h1" gutterBottom>
        Notifications
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Submission, registration-review, and pricing decisions appear here.
        Email delivery is not yet enabled.
      </Typography>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      <Paper>
        {loading ? (
          <Box sx={{ display: "grid", minHeight: 320, placeItems: "center" }}>
            <CircularProgress aria-label="Loading notifications" />
          </Box>
        ) : (
          <TableContainer sx={{ minHeight: 320 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Status</TableCell>
                  <TableCell>Notification</TableCell>
                  <TableCell>Registration</TableCell>
                  <TableCell>Date and time</TableCell>
                  <TableCell>Action</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(data?.items ?? []).map((notification) => (
                  <TableRow key={notification.id}>
                    <TableCell>
                      <Chip
                        size="small"
                        label={notification.is_read ? "Read" : "Unread"}
                        color={notification.is_read ? "default" : "primary"}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography fontWeight={notification.is_read ? 400 : 700}>
                        {notification.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {notification.message}
                      </Typography>
                    </TableCell>
                    <TableCell>{notification.registration_reference}</TableCell>
                    <TableCell>
                      {formatTimestamp(notification.created_at)}
                    </TableCell>
                    <TableCell>
                      <Button
                        onClick={() =>
                          openNotification(
                            notification.id,
                            notification.registration_id,
                          )
                        }
                      >
                        View registration
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {!data?.items.length && (
                  <TableRow>
                    <TableCell colSpan={5} align="center" sx={{ height: 240 }}>
                      No notifications yet.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
        <TablePagination
          component="div"
          count={data?.total ?? 0}
          page={page}
          rowsPerPage={pageSize}
          onPageChange={(_, nextPage) => {
            setLoading(true);
            setError("");
            setPage(nextPage);
          }}
          onRowsPerPageChange={(event) => {
            setLoading(true);
            setError("");
            setPageSize(Number(event.target.value));
            setPage(0);
          }}
          rowsPerPageOptions={[10, 25, 50]}
        />
      </Paper>
    </Container>
  );
}
