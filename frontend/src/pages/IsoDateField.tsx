import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import dayjs from "dayjs";

const ISO_DATE = "YYYY-MM-DD";

// The browser date input follows the operating system locale, so use a picker
// that always shows the portal's YYYY-MM-DD format.
export default function IsoDateField({
  label,
  value,
  onChange,
  required = true,
  helperText,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  helperText?: string;
}) {
  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <DatePicker
        label={label}
        format={ISO_DATE}
        value={value ? dayjs(value) : null}
        onChange={(date) =>
          onChange(date?.isValid() ? date.format(ISO_DATE) : "")
        }
        enableAccessibleFieldDOMStructure={false}
        slotProps={{ textField: { fullWidth: true, required, helperText } }}
      />
    </LocalizationProvider>
  );
}
