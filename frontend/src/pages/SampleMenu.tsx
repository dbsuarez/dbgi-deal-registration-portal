import BugReportIcon from "@mui/icons-material/BugReport";
import {
  IconButton,
  ListSubheader,
  Menu,
  MenuItem,
  Tooltip,
} from "@mui/material";
import { useState } from "react";

// The developer-mode bug button: a menu of sample texts that fill a text box.
export default function SampleMenu({
  samples,
  onFill,
}: {
  samples: string[];
  onFill: (text: string) => void;
}) {
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  return (
    <>
      <Tooltip title="Fill a sample (developer mode only)">
        <IconButton
          size="small"
          aria-label="Fill a sample"
          aria-haspopup="menu"
          onClick={(event) => setAnchor(event.currentTarget)}
          sx={{ color: "warning.main", p: 0.25 }}
        >
          <BugReportIcon fontSize="small" />
        </IconButton>
      </Tooltip>
      <Menu
        anchorEl={anchor}
        open={anchor !== null}
        onClose={() => setAnchor(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        transformOrigin={{ vertical: "top", horizontal: "right" }}
        slotProps={{ paper: { sx: { maxWidth: 420 } } }}
      >
        <ListSubheader sx={{ lineHeight: 2.5 }}>
          Fill a sample (developer mode)
        </ListSubheader>
        {samples.map((sample) => (
          <MenuItem
            key={sample}
            onClick={() => {
              onFill(sample);
              setAnchor(null);
            }}
            sx={{ whiteSpace: "normal", typography: "body2" }}
          >
            {sample}
          </MenuItem>
        ))}
      </Menu>
    </>
  );
}
