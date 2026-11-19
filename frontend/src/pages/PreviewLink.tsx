import DownloadIcon from "@mui/icons-material/Download";
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Link,
  type LinkProps,
} from "@mui/material";
import { useState, type ReactNode } from "react";

// The browser can show these; Word and Excel files can only be downloaded.
const PDF = /\.pdf$/i;
const PICTURE = /\.(png|jpe?g)$/i;

type Props = {
  // The file's download address; ?inline=1 asks the server to show it instead.
  url: string;
  name: string;
  children: ReactNode;
  sx?: LinkProps["sx"];
};

/** A document link that opens a preview box. Download stays available inside the box. */
export default function PreviewLink({ url, name, children, sx }: Props) {
  const [open, setOpen] = useState(false);
  const inline = `${url}${url.includes("?") ? "&" : "?"}inline=1`;
  return (
    <>
      <Link
        component="button"
        type="button"
        onClick={() => setOpen(true)}
        sx={{ textAlign: "left", verticalAlign: "baseline", ...sx }}
      >
        {children}
      </Link>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        fullWidth
        maxWidth="lg"
      >
        <DialogTitle sx={{ wordBreak: "break-all" }}>{name}</DialogTitle>
        <DialogContent dividers sx={{ p: 0 }}>
          {PDF.test(name) ? (
            <Box
              component="iframe"
              title={`Preview of ${name}`}
              src={inline}
              sx={{
                border: 0,
                width: "100%",
                height: "75vh",
                display: "block",
              }}
            />
          ) : PICTURE.test(name) ? (
            <Box sx={{ p: 2, textAlign: "center" }}>
              <Box
                component="img"
                src={inline}
                alt={`Preview of ${name}`}
                sx={{ maxWidth: "100%", maxHeight: "75vh" }}
              />
            </Box>
          ) : (
            <Alert severity="info" sx={{ m: 2 }}>
              This file type cannot be shown in the browser. Download it to open
              it.
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button
            component="a"
            href={url}
            download={name}
            startIcon={<DownloadIcon />}
          >
            Download
          </Button>
          <Button variant="contained" onClick={() => setOpen(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
