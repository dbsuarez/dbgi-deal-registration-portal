/**
 * Props that show a grey sample inside an empty text box ("For example: ..."), so people know what to type.
 * The label stays above the box, so the sample shows before the box is clicked. Typing replaces it.
 * Spread it into a TextField: <TextField label="Reason" {...example("The bidding was postponed.")} />
 */
export function example(text: string) {
  return {
    placeholder: `For example: ${text}`,
    slotProps: { inputLabel: { shrink: true } },
  };
}
