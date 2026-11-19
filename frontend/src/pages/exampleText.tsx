import { InputAdornment } from "@mui/material";

import SampleMenu from "./SampleMenu";

type DebugFill = {
  // Only in developer mode (Django DEBUG): session.is_debug.
  debug: boolean;
  onFill: (text: string) => void;
  // More samples to choose from, after the main one.
  more?: string[];
};

/**
 * Props that show a grey sample inside an empty text box ("For example: ..."), so people know what to type.
 * The label stays above the box, so the sample shows before the box is clicked. Typing replaces it.
 * Spread it into a TextField: <TextField label="Reason" {...example("The bidding was postponed.")} />
 *
 * With `fill` in developer mode, a small bug button floats at the top right of the box. It opens a menu
 * of samples (the main one plus `fill.more`) that fill the box, for quick testing. Real users never see it.
 */
export function example(text: string, fill?: DebugFill) {
  const inputLabel = { shrink: true };
  if (!fill?.debug) {
    return { placeholder: `For example: ${text}`, slotProps: { inputLabel } };
  }
  const samples = [text, ...(fill.more ?? []).filter((more) => more !== text)];
  return {
    placeholder: `For example: ${text}`,
    slotProps: {
      inputLabel,
      input: {
        // Room on the right so text never runs under the button.
        sx: { pr: 5 },
        endAdornment: (
          <InputAdornment
            position="end"
            sx={{ position: "absolute", top: 14, right: 6, m: 0 }}
          >
            <SampleMenu samples={samples} onFill={fill.onFill} />
          </InputAdornment>
        ),
      },
    },
  };
}
